import requests
import json
from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class AiosellConnector(models.TransientModel):
    _name = 'aiosell.connector'
    _description = 'Aiosell Connector'

    line_ids = fields.One2many('aiosell.connector.line', 'connector_id')
    action_type = fields.Selection(selection=[
        ('update_inventory', 'Update Inventory'),
        ('update_rate', 'Update Rates'),
    ], required=True, default='update_inventory')
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    room_type_ids = fields.Many2many('room.type', string='Room Types', domain="[('company_id', '=', company_id)]")
    rate_plan_ids = fields.Many2many('hotel.rate.plan', string='Rate Plans', domain="[('company_id', '=', company_id)]")
    folio_id = fields.Many2one('booking.folio')

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise ValidationError(_('To date cannot be earlier than from date!'))

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        if self.action_type == 'update_inventory':
            lines = self.get_inventory()
            for line in lines:
                self.line_ids = [(0, 0, {
                    'date': line['date'],
                    'room_type_id': line['roomCode'],
                    'qty_available': line['available'],
                })]
        else:
            lines = self.get_rate()
            for line in lines:
                self.line_ids = [(0, 0, {
                    'date': line['date'],
                    'room_type_id': line['roomCode'],
                    'rate_plan_id': line['rateplanCode'],
                    'rate': line['rate'],
                })]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Aiosell Connector'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'aiosell.connector',
            'res_id': self.id,
            'target': 'current'
        }

    def button_update_inventory(self):
        url = "https://live.aiosell.com/api/v2/cm/update/hotels-task"

        data = {
            "hotelCode": self.company_id.aiosell_code,
            "updates": self.prepare_rooms()
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=data)
        txt = json.loads(response.content)
        folio = self.folio_id
        self.env['audit.trails'].create({
            'booking_id': folio.booking_id.id if folio else False,
            'folio_id': folio.id if folio else False,
            'user_id': self.env.user.id,
            'operation': 'aiosell',
            'datetime': fields.Datetime.now(),
            'notes': txt.get('message', False)
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Response',
                'message': txt.get('message', False),
                'sticky': False,
            }
        }

    def prepare_rooms(self):
        vals = []
        for line in self.line_ids:
            date = line.date.strftime('%Y-%m-%d')
            vals.append({
                "startDate": date,
                "endDate": date,
                "rooms": [
                    {
                        "available": line.qty_available,
                        "roomCode": line.room_type_id.aiosell_code
                    }
                ]
            })
        return vals

    def get_inventory(self):
        vals = []
        start = self.date_from
        end = self.date_to
        if self.room_type_ids:
            room_types = self.room_type_ids
        else:
            room_types = self.env['room.type'].search([])
        while start <= end:
            for room_type in room_types:
                hotel_id = self.company_id.related_hotel_id
                rooms = self.env['hotel.room'].search([('hotel_id', '=', hotel_id.id), ('room_type', '=', room_type.id)])
                total_rooms = len(rooms)
                booked_rooms = self.get_booked_inventory(room_type, rooms.ids, start)
                available_rooms = int(total_rooms - booked_rooms)
                if available_rooms > 1:
                    vals.append({
                        'date': start,
                        'roomCode': room_type.id,
                        'available': available_rooms
                    })
            start += relativedelta(days=1)
        if vals:
            return vals

    def get_booked_inventory(self, room_type, rooms, day):
        """
            get booked qty for a specific day
        """
        booked_folios = 0
        if day:
            # arrival
            check_in_folios = self.env['booking.folio'].sudo().search([
                ('state', 'in', ['confirmed', 'draft']), ('company_id', '=', self.company_id.id),
                ('check_in', '!=', False), ('check_in_date', '=', day), ('room_type_id', '=', room_type.id)
            ])
            # departure
            check_out_folios = self.env['booking.folio'].sudo().search([
                ('room_id', '!=', False), ('company_id', '=', self.company_id.id),
                ('state', '=', 'checked_in'), ('check_in', '!=', False),
                ('check_out_date', '=', day), ('room_id', 'in', rooms), ('room_type_id', '=', room_type.id)
            ])
            exp_check_out_folios = self.env['booking.folio'].sudo().search([
                ('company_id', '=', self.company_id.id), ('state', '!=', 'cancelled'),
                ('check_in', '!=', False), ('check_out_date', '=', day), ('room_type_id', '=', room_type.id)
            ])
            exp_inhouse_folios = self.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', '=', self.company_id.id), ('state', '!=', 'cancelled'), ('room_type_id', '=', room_type.id),
                ('id', 'not in', check_out_folios.ids), ('id', 'not in', exp_check_out_folios.ids), ('id', 'not in', check_in_folios.ids)
            ]).filtered(lambda f:  f.check_in_date <= day <= f.check_out_date)

            booked_folios = len(check_in_folios) + len(exp_inhouse_folios)
        return booked_folios

    def get_rate(self):
        vals = []
        start = self.date_from
        end = self.date_to
        while start <= end:
            if self.rate_plan_ids:
                rate_plans = self.rate_plan_ids.filtered(lambda p: p.aiosell_code)
            else:
                rate_plans = self.env['hotel.rate.plan'].search([
                    ('company_id', '=', self.company_id.id), ('aiosell_code', '!=', False)
                ])

            for rate_plan in rate_plans:
                rate = rate_plan.rock_rate
                price_line = rate_plan.day_price_ids.filtered(lambda d: d.date == start)
                if price_line:
                    rate = price_line[0].price
                vals.append({
                    "date": start,
                    "roomCode": rate_plan.room_type_id.id,
                    "rate": rate,
                    "rateplanCode": rate_plan.id
                })
            start += relativedelta(days=1)
        return vals

    def button_update_rate(self):
        url = "https://live.aiosell.com/api/v2/cm/update-rates/hotels-task"
        data = {
            "hotelCode": self.company_id.aiosell_code,
            "updates": self.prepare_rates(),
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=data)
        txt = json.loads(response.content)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Response',
                'message': txt.get('message', False),
                'sticky': False,
            }
        }

    def prepare_rates(self):
        vals = []
        for line in self.line_ids.filtered(lambda l: l.rate_plan_id.aiosell_code):
            date = line.date.strftime('%Y-%m-%d')
            vals.append({
                    "startDate": date,
                    "endDate": date,
                    "rates": [
                        {
                            "roomCode": line.room_type_id.aiosell_code,
                            "rate": line.rate,
                            "rateplanCode": line.rate_plan_id.aiosell_code
                        }
                    ]
                })
        return vals


class AiosellConnectorLine(models.TransientModel):
    _name = 'aiosell.connector.line'
    _description = 'Aiosell Connector Line'

    connector_id = fields.Many2one('aiosell.connector')
    room_type_id = fields.Many2one('room.type')
    qty_available = fields.Integer()
    date = fields.Date()
    rate_plan_id = fields.Many2one('hotel.rate.plan')
    rate = fields.Float()
