from odoo import fields, models, api, _
from datetime import datetime


class FolioFilter(models.TransientModel):
    _name = 'folio.filter'
    _description = 'Folio Filter'
    _rec_name = 'rec_name'

    line_ids = fields.One2many('folio.filter.line', 'wizard_id')
    filter_type = fields.Selection(selection=[
        ('manual', 'Manual'),
        ('arrival', 'Today Arrival'),
        ('departure', 'Today Departure'),
        ('inhouse', 'Today In-house'),
    ], required=True)
    partner_id = fields.Many2one('res.partner', string='Guest Name')
    balance = fields.Monetary(related='partner_id.balance')
    currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)
    mobile = fields.Char(string='Guest Mobile')
    booking_id = fields.Many2one('hotel.booking', string='Booking Number')
    folio_id = fields.Many2one('booking.folio', string='Ref')
    reference_number = fields.Char("Reference Number")
    room_id = fields.Many2one('hotel.room', string='Room Number')
    check_in_from = fields.Date()
    check_in_to = fields.Date()
    check_out_from = fields.Date()
    check_out_to = fields.Date()
    booking_source = fields.Selection(selection=[
        ('online_agent', 'Online Travel Agent'),
        ('company', 'Company'),
        ('direct', 'Direct'),
        ('government_booking', 'Government Booking'),
        ('contract_booking', 'Contract Booking'),
        ('allotment_booking', 'Allotment Booking'),
      ])
    online_travel_agent_source = fields.Many2one('res.partner', domain="[('online_travel_agent', '=', True)]")
    company_booking_source = fields.Many2one('res.partner', domain="[('travel_type', '=', 'company')]")
    state_ids = fields.Many2many('folio.report.state', string='States')
    related_hotel = fields.Many2many('hotel.hotel', string='Related Hotel')
    rec_name = fields.Char(default='Front Office Operations')
    pending_orders = fields.Integer(compute='_compute_orders_total')
    complete_orders = fields.Integer(compute='_compute_complete_orders')
    include_cancelled = fields.Boolean()

    advanced_search = fields.Boolean("Advanced Search")

    day_use = fields.Boolean("Day Use")
    complimentary_room = fields.Boolean("Complimentary Room")
    house_use = fields.Boolean("House Use")

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        if self.check_in_from:
            domain.append(('check_in_date', '>=', self.check_in_from))
        if self.check_in_to:
            domain.append(('check_in_date', '<=', self.check_in_to))
        if self.check_out_from:
            domain.append(('check_out_date', '>=', self.check_out_from))
        if self.check_out_to:
            domain.append(('check_out_date', '<=', self.check_out_to))
        if self.booking_source:
            domain.append(('booking_id.booking_source', '=', self.booking_source))
            if self.booking_source == 'online_agent' and self.online_travel_agent_source:
                domain.append(('booking_id.online_travel_agent_source', '=', self.online_travel_agent_source.id))
            elif self.booking_source == 'company' and self.company_booking_source:
                domain.append(('booking_id.company_booking_source', '=', self.company_booking_source.id))
        if self.state_ids:
            domain.append(('state', 'in', self.state_ids.mapped('type')))
        if self.reference_number:
            domain.append(('booking_id.ref', 'ilike', self.reference_number))
        if self.related_hotel:
            domain.append(('hotel_id', 'in', self.related_hotel.ids))
        if self.day_use:
            domain.append(('day_use', '=', self.day_use))
        if self.complimentary_room:
            domain.append(('complimentary_room', '=', self.complimentary_room))
        if self.house_use:
            domain.append(('house_use', '=', self.house_use))
        folios = self.env['booking.folio'].sudo().search(domain)

        audit_date_start = datetime.combine(self.env.company.audit_date, datetime.strptime('000000', '%H%M%S').time())
        audit_date_end = datetime.combine(self.env.company.audit_date, datetime.strptime('235959', '%H%M%S').time())
        if self.filter_type == 'arrival':
            folios = self.env['booking.folio'].sudo().search([
                ('state', 'in', ['confirmed', 'draft']), ('check_in', '!=', False),
                ('company_id', '=', self.env.company.id), ('id', 'in', folios.ids)
            ]).filtered(
                lambda f: audit_date_end >= f.check_in >= audit_date_start
            )
        elif self.filter_type == 'manual':
            folios = self.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', '=', self.env.company.id), ('id', 'in', folios.ids)
            ])
        elif self.filter_type == 'departure':
            folios = self.env['booking.folio'].sudo().search([
                ('state', '=', 'checked_in'), ('check_in', '!=', False),
                ('company_id', '=', self.env.company.id), ('id', 'in', folios.ids)
            ]).filtered(
                lambda f: audit_date_end >= f.check_out >= audit_date_start
            )
        else:
            departure_folios = self.env['booking.folio'].sudo().search([
                ('state', '=', 'checked_in'), ('check_in', '!=', False),
                ('company_id', '=', self.env.company.id)
            ]).filtered(
                lambda f: audit_date_end >= f.check_out >= audit_date_start
            )
            folios = self.env['booking.folio'].sudo().search([
                ('state', '=', 'checked_in'), ('check_in', '!=', False), ('id', 'not in', departure_folios.ids),
                ('company_id', '=', self.env.company.id), ('id', 'in', folios.ids)
            ])
        if self.partner_id:
            folios = folios.filtered(lambda f: f.partner_id.id == self.partner_id.id)
        if self.booking_id:
            folios = folios.filtered(lambda f: f.booking_id.id == self.booking_id.id)
        if self.folio_id:
            folios = folios.filtered(lambda f: f.id == self.folio_id.id)
        if self.room_id:
            folios = folios.filtered(lambda f: f.room_id.id == self.room_id.id)
        if self.mobile:
            folios = self.env['booking.folio'].search([
                ('id', 'in', folios.ids), ('partner_id.mobile', 'ilike', self.mobile)
            ])
        if not self.include_cancelled:
            folios = folios.filtered(lambda f: f.state != 'cancelled')

        for folio in folios:
            self.line_ids = [(0, 0, {'folio_id': folio.id})]

    def print_pdf(self):
        return self.env.ref('hotel_booking_folio.action_folio_filter_report').report_action(self)

    def button_create_booking(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Booking",
            'res_model': 'hotel.booking',
            'view_mode': 'form',
            'target': 'current',
        }

    def button_create_work_orders(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Work Orders",
            'res_model': 'hotel.work.order',
            'view_mode': 'form',
            'target': 'current',
        }

    def button_out_of_order(self):
        out_of_order = self.env.ref('hotel_booking.out_of_order_action').read()[0]
        return out_of_order

    def action_open_pending_orders(self):
        pending_work_order = self.env.ref('hotel_booking.pending_hotel_work_order_action').read()[0]
        return pending_work_order

    @api.onchange('booking_id', 'check_in_from', 'check_out_from', 'filter_type')
    def _compute_orders_total(self):
        pending_work_order = self.env['hotel.work.order'].search([('state', '!=', 'done')])
        if pending_work_order:
            self.pending_orders = len(pending_work_order)
        else:
            self.pending_orders = 0

    def action_open_complete_orders(self):
        complete_work_order = self.env.ref('hotel_booking.complete_hotel_work_order_action').read()[0]
        return complete_work_order

    @api.onchange('booking_id', 'check_in_from', 'check_out_from', 'filter_type')
    def _compute_complete_orders(self):
        complete_work_order = self.env['hotel.work.order'].search([('state', '=', 'done')])
        if complete_work_order:
            self.complete_orders = len(complete_work_order)
        else:
            self.complete_orders = 0


class FolioFilterLine(models.TransientModel):
    _name = 'folio.filter.line'
    _description = 'Folio Filter Line'

    wizard_id = fields.Many2one('folio.filter')
    folio_id = fields.Many2one('booking.folio')
    booking_id = fields.Many2one('hotel.booking', related='folio_id.booking_id', store=True)
    ref = fields.Char(related='booking_id.ref')
    company_booking_source = fields.Many2one('res.partner', related='booking_id.company_booking_source')
    customer_credit_limit = fields.Monetary(related='company_booking_source.customer_credit_limit')
    balance = fields.Monetary(related='company_booking_source.balance')
    name = fields.Char(related='folio_id.name')
    partner_id = fields.Many2one('res.partner', related='folio_id.partner_id')
    room_type_id = fields.Many2one('room.type', related='folio_id.room_type_id')
    rate_plan_id = fields.Many2one('hotel.rate.plan', related='folio_id.rate_plan_id')
    room_id = fields.Many2one('hotel.room', related='folio_id.room_id')
    check_in = fields.Datetime(related='folio_id.check_in')
    check_out = fields.Datetime(related='folio_id.check_out')
    price_subtotal = fields.Monetary(related='folio_id.price_subtotal')
    price_total = fields.Monetary(related='folio_id.price_total')
    price_tax = fields.Monetary(related='folio_id.price_tax')
    price_paid = fields.Monetary(related='folio_id.price_paid')
    price_due = fields.Monetary(related='folio_id.price_due')
    currency_id = fields.Many2one('res.currency', related='booking_id.currency_id')
    state = fields.Selection(related='folio_id.state')
    related_hotel = fields.Many2many('hotel.hotel', string='Related Hotel')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    total_nights = fields.Integer(related='folio_id.total_nights')
    number_of_guests = fields.Integer(related='folio_id.number_of_guests')

    def button_open_lines(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Folio",
            'res_model': 'booking.folio',
            'res_id': self.folio_id.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def button_open_booking(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Booking",
            'res_model': 'hotel.booking',
            'res_id': self.booking_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def print_report(self):
        return self.env.ref('hotel_booking.folio_report_action').report_action(self.folio_id)

    # one2many widget methods
    @api.model
    def action_check_in(self, lines):
        filter_lines = self.env['folio.filter.line'].browse(lines)
        folios = filter_lines.mapped('folio_id')
        for folio in folios.filtered(lambda f: f.state in ['draft', 'confirmed']):
            msg = folio.js_validate_check_in(folio.room_id)
            if msg:
                return {'error': msg}
            folio.with_context(called_from_js=True).button_check_in()
        return True

    @api.model
    def action_check_out(self, lines):
        filter_lines = self.env['folio.filter.line'].browse(lines)
        folios = filter_lines.mapped('folio_id')
        for folio in folios.filtered(lambda f: f.state in ['checked_in']):
            if not folio.today_is_checkout:
                return {'error': f'{folio.name} check out is not today!'}
            msg = folio.js_validate_check_out()
            if msg:
                return {'error': msg}
            folio.button_check_out()
        return True

    def action_register_payment(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'booking.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {
                'default_booking': self.folio_id.booking_id.id,
                'default_partner_id': self.partner_id.id,
                'default_folio_id': self.folio_id.id,
                'default_payment_type': 'inbound',
                'default_amount': self.folio_id.price_due,
                'default_partner_type': 'customer',
                'default_communication': self.folio_id.name.replace('BK', 'FO'),
                'default_audit_date': self.company_id.audit_date,
                'default_company_booking_source_ids': [(4, self.booking_id.company_booking_source.id)] if self.booking_id.company_booking_source else False
            }
        }

    # def button_change_room(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': "Change Room",
    #         'res_model': 'folio.change.room',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_folio_id': self.folio_id.id,
    #             'default_room_type_id': self.room_type_id.id,
    #             'default_old_room_id': self.room_id.id,
    #             'default_check_in': self.check_in,
    #             'default_check_out': self.check_out,
    #         }
    #     }

    def button_change_room(self):
        available_room_ids = self.env['hotel.room'].browse(self.get_available_rooms()).filtered(
            lambda r: r.stay_state.id == self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id).ids
        charged_line_ids = self.folio_id.line_ids.filtered(lambda l: l.type == 'room_charge').ids
        has_charge_access = True if self.env.user.has_group(
            'hotel_booking_folio.group_change_room_charge_user') else False
        return {
            'type': 'ir.actions.act_window',
            'name': "Change Room",
            'res_model': 'folio.change.room',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_folio_id': self.folio_id.id,
                'default_room_type_id': self.room_type_id.id,
                'default_old_room_id': self.room_id.id,
                'default_check_in': self.check_in,
                'default_check_out': self.check_out,
                'default_available_room_ids': [(6, 0, available_room_ids)],
                'default_charged_line_ids': [(6, 0, charged_line_ids)],
                'default_has_charge_access': has_charge_access,
            }
        }

    def get_available_rooms(self, check_in_date=False, check_out_date=False):
        '''
        There are 3 cases of overlapping to consider:

        s1   s2   e1   e2
        (    [----)----]
        s2   s1   e2   e1
        [----(----]    )
        s1   s2   e2   e1
        (    [----]    )
        '''

        available_rooms = []
        check_in_date = check_in_date if check_in_date else self.check_in
        check_out_date = check_out_date if check_out_date else self.check_out
        out_of_order_rooms = self.env["hotel.room"].search([
            ('room_type', '=', self.room_type_id.id),
            '|', '|',
            '&', ('out_of_order_from', '<=', check_in_date), ('out_of_order_to', '>', check_in_date),
            '&', ('out_of_order_from', '<=', check_out_date), ('out_of_order_to', '>', check_out_date),
            '&', ('out_of_order_from', '<=', check_in_date), ('out_of_order_to', '>', check_out_date),
        ])
        rooms = self.env["hotel.room"].search([
            ('room_type', '=', self.room_type_id.id), ('id', 'not in', out_of_order_rooms.ids)
        ])

        for room in rooms:
            # s1 = check_in_date # s2 = self.check_in_date
            # e1 = check_out_date # e2 = self.check_out_date
            domain = [
                ('id', '!=', self.folio_id.id),
                ('company_id', '=', self.company_id.id),
                ('room_id', '=', room.id),
                ('state', 'in', ['part_checked_in', 'checked_in', 'confirmed', 'draft']),
                '|', '|',
                '&', ('check_in_date', '<=', check_in_date), ('check_out_date', '>', check_in_date),
                '&', ('check_in_date', '<=', check_out_date), ('check_out_date', '>', check_out_date),
                '&', ('check_in_date', '<=', check_in_date), ('check_out_date', '>', check_out_date),
            ]
            folio = self.env['booking.folio'].search(domain)
            if not folio:
                available_rooms.append(room.id)
        return available_rooms
