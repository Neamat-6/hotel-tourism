import requests
import json
from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, _logger


class EzeeConnector(models.TransientModel):
    _name = 'ezee.connector'
    _description = 'Ezee Connector'

    line_ids = fields.One2many('ezee.connector.line', 'connector_id')
    action_type = fields.Selection(selection=[
        ('update_inventory', 'Update Inventory'),
        ('update_rate', 'Update Rates'),
    ], required=True, default='update_inventory')
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    room_type_ids = fields.Many2many('room.type', string='Room Types', domain="[('company_id', '=', company_id), ('ezee_room_type_id', '!=', False)]")
    rate_plan_ids = fields.Many2many('hotel.rate.plan', string='Rate Plans', domain="[('company_id', '=', company_id)]")
    folio_id = fields.Many2one('booking.folio')
    note = fields.Text()

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
                    'date_from': line['dateFrom'],
                    'date_to': line['dateTo'],
                    'room_type_id': line['roomType'],
                    'room_code': line['roomTypeID'],
                    'qty_available': line['available'],
                })]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ezee Connector'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'ezee.connector',
            'res_id': self.id,
            'target': 'current'
        }

    def get_inventory(self):
        vals = []
        start = self.date_from
        end = self.date_to
        if self.room_type_ids:
            room_types = self.room_type_ids
        else:
            room_types = self.env['room.type'].search([('ezee_room_type_id', '!=', False)])
        while start <= end:
            for room_type in room_types:
                hotel_id = self.company_id.related_hotel_id
                rooms = self.env['hotel.room'].search([('hotel_id', '=', hotel_id.id), ('room_type', '=', room_type.id)])
                total_rooms = len(rooms)
                out_of_order_rooms = self.env['hotel.room'].search([
                    ('id', 'in', rooms.ids),
                    '|',
                    '&', ('out_of_order_from', '<=', end),
                    ('out_of_order_to', '>=', start),
                    '&', ('out_of_order_from', '<=', start),
                    ('out_of_order_to', '>=', end)
                ])
                out_of_order_room_ids = out_of_order_rooms.ids

                booked_rooms = self.get_booked_inventory(room_type, rooms.ids, start)
                available_rooms = int(total_rooms - booked_rooms - len(out_of_order_room_ids))
                vals.append({
                    'dateFrom': start,
                    'dateTo': start,
                    'roomType': room_type.id,
                    'roomTypeID': room_type.ezee_room_type_id.code,
                    'available': available_rooms
                })
            start += relativedelta(days=1)
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

    def button_update_inventory(self):
        hotel = self.company_id.related_hotel_id
        base_url = hotel.ezee_base_url
        url = f"{base_url}pmsinterface/pms_connectivity.php"
        data = {
            "RES_Request": {
                "Request_Type": "UpdateAvailability",
                "Authentication": {
                    "HotelCode": hotel.ezee_hotel_code,
                    "AuthCode": hotel.ezee_api_key
                },
                "RoomType": self.prepare_rooms()
            }
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=data)
        txt = json.loads(response.content)
        if txt.get('Success', False):
            msg = txt['Success']['SuccessMsg']
        else:
            msg = txt['Errors']['ErrorMessage']
        self.note = msg
        _logger.info(f"++++++++++ update_inventory {msg} ++++++")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Response',
                'message': msg,
                'sticky': False,
            }
        }

    def prepare_rooms(self):
        vals = []
        for line in self.line_ids:
            vals.append({
                "RoomTypeID": line.room_code,
                "FromDate": line.date_from.strftime('%Y-%m-%d'),
                "ToDate": line.date_to.strftime('%Y-%m-%d'),
                "Availability": str(line.qty_available),
            })
        return vals


class EzeeConnectorLine(models.TransientModel):
    _name = 'ezee.connector.line'
    _description = 'Ezee Connector Line'

    connector_id = fields.Many2one('ezee.connector')
    room_type_id = fields.Many2one('room.type')
    room_code = fields.Char()
    qty_available = fields.Integer()
    date_from = fields.Date()
    date_to = fields.Date()
    rate_plan_id = fields.Many2one('hotel.rate.plan')
    rate = fields.Float()
