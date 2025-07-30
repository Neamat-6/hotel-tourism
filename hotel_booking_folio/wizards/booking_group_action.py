from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)


class BookingGroupAction(models.TransientModel):
    _name = 'booking.group.action'
    _description = 'Booking Group Action'

    booking_id = fields.Many2one('hotel.booking')
    company_id = fields.Many2one('res.company', related='booking_id.company_id', store=True)
    type = fields.Selection(selection=[
        ('assign', 'Group Assign Room'),
        ('check_in', 'Group Check In'),
        ('check_out', 'Group Check Out'),
        ('discount', 'Group Discount'),
        ('amend', 'Group Amend'),
        ('charge', 'Group Checkout Charge'),
        ('update_room_charge', 'Group Update Room Charge'),
    ], required=True)
    floor_start = fields.Many2one('hotel.floor', string='From Floor')
    floor_start_sequence = fields.Integer(related='floor_start.sequence', store=True)
    floor_end = fields.Many2one('hotel.floor', string='To Floor', domain="[('sequence', '>=', floor_start_sequence)]")
    assign_clean_room = fields.Boolean(string='Assign Only Clean Room')
    assign_type = fields.Selection(selection=[
        ('auto', 'Auto'),
        ('manual', 'Manual'),
    ], default='auto', string='Type')
    discount_id = fields.Many2one('booking.discount')
    discount_rule = fields.Selection(selection=[
        ('all_nights', 'All Nights'),
        ('first_night', 'First Night'),
        ('last_night', 'Last Night'),
    ])
    note = fields.Char("Note")
    folio_ids = fields.Many2many('booking.folio',
                                 domain="[('booking_id', '=', booking_id), ('state', 'in', ['draft', 'confirmed'])]")
    all_folio_ids = fields.Many2many('booking.folio', 'booking_group_action_folio_rel',
                                     'wizard_id', 'folio_id', domain="[('booking_id', '=', booking_id)]")
    checkout_folio_ids = fields.Many2many('booking.folio', 'booking_group_action_out_folio_rel',
                                          'wizard_id2', 'out_folio_id', domain="[('booking_id', '=', booking_id)]")
    checkin_folio_ids = fields.Many2many('booking.folio', 'booking_group_action_in_folio_rel',
                                         'checkin_id2', 'in_folio_id', domain="[('booking_id', '=', booking_id)]")
    amend_folio_ids = fields.Many2many('booking.folio', 'booking_group_action_amend_folio_rel',
                                       'amend_wizard_id', 'amend_folio_id', domain="[('booking_id', '=', booking_id)]")
    charge_folio_ids = fields.Many2many('booking.folio', 'booking_group_action_charge_folio_rel',
                                        'charge_wizard_id', 'charge_folio_id',
                                        domain="[('booking_id', '=', booking_id)]")
    new_room_charge = fields.Float()
    all_room_ids = fields.Many2many('hotel.room', 'booking_group_action_room_rel', 'wizard_id', 'room_id',
                                    string='Rooms')
    room_ids = fields.Many2many('hotel.room', string='Rooms', domain="[('id', 'in', all_room_ids)]")
    all_folio_line_ids = fields.Many2many('booking.folio.line', 'booking_group_action_folio_line_rel', 'wizard_id',
                                          'folio_line_id')
    folio_line_ids = fields.Many2many('booking.folio.line', string='Folio Lines',
                                      domain="[('id', 'in', all_folio_line_ids)]")
    price_include_tax = fields.Boolean(default=True, readonly=True)
    tax_ids = fields.Many2many('account.tax')
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    unassign = fields.Boolean()
    open_discount = fields.Boolean(related='discount_id.open_discount')
    discount_percentage = fields.Float(string="Discount %")

    def button_unassign_rooms(self):
        for folio in self.folio_ids.filtered(lambda f: f.state in ['draft', 'confirmed']):
            folio.room_id.write({
                'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
            })
            folio.with_context(ignore_updates=True).write({
                'room_id': False
            })
        message = f'Rooms Unassigned Successfully'
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
        }
        # return self.button_refresh()

    def button_manual_assign(self):
        for folio in self.folio_ids:
            folio.write({'group_action_wizard': self.id})
        return {
            'type': 'ir.actions.act_window',
            'name': "Group Action",
            'res_model': 'booking.group.action',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id
        }

    def button_auto_assign(self):
        logger.info('auto assign from extend')
        start = self.floor_start_sequence
        end = self.floor_end.sequence
        company_id = self.booking_id.company_id.id
        folio_ids = self.folio_ids.filtered(lambda f: not f.room_id)
        folios = [folio.id for folio in folio_ids]

        clean = self.env.ref('hotel_booking.hotel_room_status_clean').id
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        # logger.info(f'floor_end {self.floor_end.id}')
        # logger.info(f'Start: {start} -- End: {end}')
        # logger.info(f'Company: {company_id}')
        # logger.info(f'Folios: {folios}')
        assigned_rooms = []
        if not folio_ids:
            raise ValidationError("There is no folios not assigned room")
        first_folio = folio_ids[0]
        current_check_in = first_folio.check_in_date
        current_check_out = first_folio.check_out_date
        current_room_type = first_folio.room_type_id
        current_state = first_folio.state
        available_rooms = first_folio.get_available_rooms()
        # logger.info(f'First Folio: {first_folio}')
        # logger.info(f'available_rooms {available_rooms}')
        # logger.info(f'current_check_in {current_check_in}')
        for i in range(start, end+1):
            # logger.info(f'Sequence: {i}')
            floor = self.env['hotel.floor'].search([('company_id', '=', company_id), ('sequence', '=', i)])
            for folio in folio_ids:
                if folio.id in folios:
                    # logger.info(f'folio {folio}')
                    # if folios shared same checkin, out, room type and state-> no need to call get_available_rooms
                    # we can call it once and exclude assigned rooms
                    if folio.check_in_date != current_check_in or folio.check_out_date != current_check_out or folio.room_type_id != current_room_type or folio.state != current_state:
                        logger.info('hhhhhhhhhhhhhhhhhhhhh in if condition')
                        current_check_in = folio.check_in_date
                        current_check_out = folio.check_out_date
                        current_room_type = folio.room_type_id
                        current_state = folio.state
                        available_rooms = folio.get_available_rooms()
                        logger.info(f'available_rooms in if condition {available_rooms}')

                    floor_rooms = floor.room_ids.filtered(
                        lambda r: r.room_type.id == folio.room_type_id.id and r.stay_state.id == vacant and r.id not in assigned_rooms
                    )
                    # logger.info(f'floor_rooms {floor_rooms}')
                    if self.assign_clean_room:
                        floor_rooms = floor_rooms.filtered(lambda r: r.state.id == clean)
                        # logger.info(f'floor_rooms cleaaan {floor_rooms}')
                    intersection = list(set(floor_rooms.ids) & set(available_rooms))
                    # logger.info(f'Intersection: {intersection}')
                    if intersection:
                        old_room_id = folio.room_id
                        new_room_id = self.env['hotel.room'].browse(intersection[0])
                        # old room
                        # logger.info(f'Old Room: {old_room_id}')
                        # logger.info(f'New Room: {new_room_id}')
                        if old_room_id:
                            # logger.info(f'old_room_id.stay_state {old_room_id.stay_state.id}')
                            new_room_id.stay_state = old_room_id.stay_state.id
                        else:
                            if folio.check_in_date == folio.company_id.audit_date:
                                new_room_id.stay_state = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival').id
                                # logger.info(f'new room arrived {new_room_id}')
                            else:
                                new_room_id.stay_state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
                                # logger.info(f'new room vacant {new_room_id}')
                        # set old room to vacant
                        if old_room_id:
                            # logger.info(f'old room vacant {old_room_id}')
                            old_room_id.stay_state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id

                        folio.with_context(ignore_updates=True).write({
                            'room_id': intersection[0]
                        })
                        assigned_rooms.append(intersection[0])
                        folios.remove(folio.id)
                    else:
                        continue
                    if not folios:
                        break
        message = f'Rooms Assigned Successfully'
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
        }

    def button_group_check_in(self):
        for folio in self.checkin_folio_ids:
            folio.with_context(ignore_updates=True, called_from_group_action=True).button_check_in()
        message = f'{self.booking_id.name} Checked In Successfully'
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
        }
        # return self.button_refresh()

    def button_group_check_out(self):
        for folio in self.checkout_folio_ids:
            folio.button_check_out()
        message = f'{self.booking_id.name} Checked Out Successfully'
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
        }
        # return self.button_refresh()

    def button_group_discount(self):
        for folio in self.all_folio_ids:
            if self.discount_id:
                if self.env.user not in self.discount_id.discount_allowed_users:
                    raise ValidationError("You Are Not Allowed To Use This Discount")
            discount_wizard = self.env['booking.apply.discount'].create({
                'folio_id': folio.id,
                'type': self.discount_id.id,
                'discount_rule': self.discount_rule,
                'note': self.note,
                'discount': self.discount_percentage
            })
            discount_wizard.apply_discount()
        message = f'Discount Done Successfully'
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
        }
        # return self.button_refresh()

    def button_group_checkout_charge(self):
        for folio in self.all_folio_ids:
            folio.button_check_out_charge()
        message = f'{self.booking_id.name} Checked Out Charge Done Successfully'
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
        }
        # return self.button_refresh()

    def button_update_room_charge(self):
        if not self.new_room_charge:
            raise ValidationError("Add new room charge!")
        if self.new_room_charge < 0.0:
            raise ValidationError("room charge is less than zero!")
        price_unit = self.new_room_charge
        old_room_charge = self.booking_id.amount_total
        price_municipality = 0
        price_vat = 0
        price_untaxed = 0
        if self.price_include_tax:
            vat = self.tax_ids.filtered(lambda t: t.type == 'vat')
            if vat:
                vat = vat[0]
                price_untaxed = (price_unit / (100 + vat.amount)) * 100
                price_vat = price_unit - price_untaxed

            municipality = self.tax_ids.filtered(lambda t: t.type == 'municipality')
            if municipality:
                price_before_municipality = price_untaxed
                municipality = municipality[0]
                price_untaxed = (price_before_municipality / (100 + municipality.amount)) * 100
                price_municipality = price_before_municipality - price_untaxed
        else:
            price_untaxed = price_unit
            price_total = price_unit
            municipality = self.tax_ids.filtered(lambda t: t.type == 'municipality')
            if municipality:
                municipality = municipality[0]
                price_total = price_unit * (municipality.amount / 100 + 1)
                price_municipality = price_total - price_unit

            vat = self.tax_ids.filtered(lambda t: t.type == 'vat')
            if vat:
                price_before_vat = price_total
                vat = vat[0]
                price_total = price_before_vat * (vat.amount / 100 + 1)
                price_vat = price_total - price_before_vat

        for line in self.folio_line_ids:
            line.write({'amount': price_untaxed})

            vat_line = line.folio_id.line_ids.filtered(
                lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax
            )
            if vat_line:
                vat_line.write({'amount': price_vat})
            elif not vat_line and price_vat:
                self.env['booking.folio.line'].create({
                    'folio_id': line.folio_id.id,
                    'day': line.day,
                    'amount': price_vat,
                    'particulars': 'VAT',
                    'type': 'tax',
                    'tax_type': 'vat',
                })

            municipality_line = line.folio_id.line_ids.filtered(
                lambda
                    l: l.day == line.day and l.type == 'tax' and l.tax_type == 'municipality' and not l.is_service_tax
            )
            if municipality_line:
                municipality_line.write({'amount': price_municipality})
            elif not municipality_line and price_municipality:
                self.env['booking.folio.line'].create({
                    'folio_id': line.folio_id.id,
                    'day': line.day,
                    'amount': price_municipality,
                    'particulars': 'Municipality',
                    'type': 'tax',
                    'tax_type': 'municipality'
                })
        if self.booking_id.payment_type_id == 'city_ledger':
            for record in self.booking_id.folio_ids:
                payment_line = record.line_ids.filtered(lambda l: l.payment_id)
                if payment_line:
                    for payment in payment_line:
                        payment.payment_id.action_draft()
                        payment.payment_id.update({'amount': record.price_total, 'is_payment': True})
                        payment.update({'amount': -record.price_total})
                        payment.payment_id.action_post()

        self.env['audit.trails'].create({
            'booking_id': self.booking_id.id,
            'user_id': self.env.user.id,
            'operation': 'change_price',
            'datetime': fields.Datetime.now(),
            'notes': f"Update Room Charge From {old_room_charge} To {self.booking_id.amount_total}"
        })
        message = f'{self.booking_id.name} Room Charge Updated Successfully'
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
        }
        # self.button_refresh()

    def button_refresh(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Group Action'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.group.action',
            'res_id': self.id,
            'target': 'new'
        }

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'charge' and not self.company_id.checkout_charge:
            raise ValidationError(f"{self.company_id.name} is not using Checkout Charge!")

    @api.onchange('price_include_tax')
    def onchange_price_include_tax(self):
        rate_plans = self.booking_id.line_ids.mapped('rate_plan')
        if self.price_include_tax:
            self.tax_ids = rate_plans.tax_ids.filtered(lambda t: t.price_include).ids
        else:
            self.tax_ids = rate_plans.tax_ids.filtered(lambda t: not t.price_include).ids

    @api.onchange('room_ids')
    def onchange_room_ids(self):
        if self.room_ids:
            self.all_folio_ids = self.env['booking.folio'].search([
                ('room_id', 'in', self.room_ids.ids), ('booking_id', '=', self.booking_id.id)
            ])

    @api.onchange('all_folio_ids')
    def onchange_all_folio_ids(self):
        if self.type == 'update_room_charge':
            self.folio_line_ids = self.all_folio_ids.mapped('line_ids').filtered(
                lambda l: l.type == 'room_charge').mapped('id')

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_to and rec.date_from:
                if rec.date_to < rec.date_from:
                    raise ValidationError(_('the to date cannot be earlier than the from date!'))

    def button_search(self):
        if not self.date_from and not self.date_to:
            raise ValidationError('please select dates!')

        self.folio_line_ids = [(5, 0, 0)]
        domain = [('id', 'in', self.all_folio_line_ids.ids)]
        if self.date_from:
            domain.append(('day', '>=', self.date_from))
        if self.date_to:
            domain.append(('day', '<=', self.date_to))
        self.folio_line_ids = self.env['booking.folio.line'].sudo().search(domain).ids

        return {
            'type': 'ir.actions.act_window',
            'name': _('Group Actions'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.group.action',
            'res_id': self.id,
            'target': 'new'
        }
