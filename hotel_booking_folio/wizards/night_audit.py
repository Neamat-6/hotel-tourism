from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from collections import defaultdict
from odoo.tools import float_round


def chunked(iterable, size):
    """Yield successive chunks of the given size from iterable."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


class NightAudit(models.TransientModel):
    _inherit = 'night.audit'

    enable_limit = fields.Boolean(default=True)
    limit = fields.Integer(default=50)
    total_folios = fields.Integer(compute='compute_folios', store=True)
    remaining_folios = fields.Integer(compute='compute_folios', store=True)

    @api.depends('folio_ids', 'folio_ids.charged')
    def compute_folios(self):
        for rec in self:
            rec.total_folios = 0
            rec.remaining_folios = 0
            if rec.folio_ids:
                rec.total_folios = len(rec.folio_ids)
                rec.remaining_folios = len(rec.folio_ids) - len(rec.folio_ids.filtered(lambda f: f.charged))

    @api.onchange('date')
    def _onchange_date(self):
        print('callllllllllllllled onchange_date')
        if self.env.context.get('allowed_company_ids', False):
            if len(self.env.context.get('allowed_company_ids')) > 1:
                raise ValidationError("You must activate one company only!")
        if self.date > date.today():
            raise ValidationError("Night Audit Date is {} and today is {}".format(self.date, date.today()))
        # draft
        draft_folio_ids = [(5, 0, 0)]
        line_fields = [f for f in self.env['night.audit.draft.booking']._fields.keys()]
        draft_folio_ids_data_tmpl = self.env['night.audit.draft.booking'].default_get(line_fields)
        draft_folios = self.env['booking.folio'].search([
            ('check_in_date', '=', self.date), ('state', 'in', ['draft', 'confirmed'])
        ])
        for folio in draft_folios:
            draft_booking_ids_data = dict(draft_folio_ids_data_tmpl)
            draft_booking_ids_data.update(self._prepare_folio_vals(folio))
            draft_folio_ids.append((0, 0, draft_booking_ids_data))
        # checkout
        checkout_folio_ids = [(5,)]
        line_fields = [f for f in self.env['night.audit.checkout.booking']._fields.keys()]
        checkout_folio_ids_data_tmpl = self.env['night.audit.checkout.booking'].default_get(line_fields)
        checkout_folios = self.env['booking.folio'].search([
            ('check_out_date', '=', self.date), ('state', '=', 'checked_in')
        ])
        for folio in checkout_folios:
            checkout_folio_ids_data = dict(checkout_folio_ids_data_tmpl)
            checkout_folio_ids_data.update(self._prepare_folio_vals(folio))
            checkout_folio_ids.append((0, 0, checkout_folio_ids_data))
        # room state
        room_state_ids = [(5, 0, 0)]
        line_fields = [f for f in self.env['night.audit.room.state']._fields.keys()]
        room_state_ids_data_tmpl = self.env['night.audit.room.state'].default_get(line_fields)
        folios = self.env['booking.folio'].search([
            ('state', 'not in', ['checked_out', 'cancelled']), ('room_id', '!=', False), '|',
            ('check_in_date', '=', self.date), ('check_out_date', '=', self.date)
        ])
        for folio in folios:
            room_state_ids_data = dict(room_state_ids_data_tmpl)
            room_state_ids_data.update(self._prepare_folio_vals(folio))
            room_state_ids.append((0, 0, room_state_ids_data))

        self.update({
            'draft_booking_ids': draft_folio_ids,
            'checkout_booking_ids': checkout_folio_ids,
            'room_state_ids': room_state_ids,
        })

    @api.model
    def _prepare_folio_vals(self, folio):
        return {
            'booking_id': folio.booking_id.id,
            'folio_id': folio.id,
            'room_id': folio.room_id.id,
            'room_type_id': folio.room_type_id.id,
        }

    @api.model
    def _prepare_folio_line_vals(self, folio_line):
        folio = folio_line.folio_id
        return {
            'booking_id': folio.booking_id.id,
            'folio_id': folio.id,
            'folio_line_id': folio_line.id,
            'room_id': folio.room_id.id,
            'description': folio_line.particulars,
        }

    def state_exit_start(self):
        for draft in self.draft_booking_ids:
            if not draft.action:
                raise ValidationError("You have to select action per line!")
            if not draft.partner_id:
                raise ValidationError("{} has no guest!".format(draft.booking_id.name))
            folio = draft.folio_id
            if draft.action == 'cancel':
                folio.cancel_reason_id = draft.cancel_reason_id.id
                folio.with_context(selected_folio=True).button_cancel()
                # folio.state = 'cancelled'
                draft.unlink()
            elif draft.action == 'check_in':
                folio.write({'room_id': draft.room_id.id})
                folio.button_check_in()
                if folio.state == 'checked_in':
                    draft.unlink()
        self.state = 'release_reservation'

    def state_exit_release_reservation(self):
        for line in self.checkout_booking_ids:
            if not line.action:
                raise ValidationError("You have to select action per line!")
            line.folio_id.button_check_out()
            if line.folio_id.state == 'checked_out':
                line.unlink()
        self.state = 'room_status'

    def state_exit_room_status(self):
        print('callllllllllllllled state_exit_room_status')
        for line in self.room_state_ids:
            # if not line.action:
            #     raise ValidationError("You have to select action per line!")
            if line.action == 'check_out':
                line.folio_id.button_check_out()
                if line.folio_id.state == 'checked_out':
                    line.unlink()
            line.room_id.write({
                'state': self.env.ref('hotel_booking.hotel_room_status_dirty').id,
            })
        # compute folios
        folio_ids = [(5, 0, 0)]
        line_fields = [f for f in self.env['night.audit.folio']._fields.keys()]
        folio_ids_data_tmpl = self.env['night.audit.folio'].default_get(line_fields)
        folio_line_ids = self.env['booking.folio.line'].search([
            ('day', '=', self.date), ('payment_id', '=', False), ('is_city_ledger', '=', False), ('type', '!=', 'tax'),
            ('folio_id.state', '=', 'checked_in'), ('folio_id.room_id', '!=', False), ('is_invoiced', '=', False)
        ])
        for folio_line in folio_line_ids:
            folio_ids_data = dict(folio_ids_data_tmpl)
            folio_ids_data.update(self._prepare_folio_line_vals(folio_line))
            folio_ids.append((0, 0, folio_ids_data))
        self.update({
            'folio_ids': folio_ids,
            'state': 'unsettled_folios'
        })

    # def state_exit_nightly_charge(self):
    #     print('callllllllllllllled state_exit_nightly_charge')
    #     if self.env.company.checkout_charge or self.env.company.related_hotel_id.unsettled_invoice:
    #         self.state = 'final'
    #         self.new_date = self.date + relativedelta(days=1)
    #     else:
    #         remain = self.remaining_folios if self.enable_limit and self.remaining_folios else 0
    #         limit = self.limit if self.enable_limit else self.total_folios
    #         if remain:
    #             folio_ids = self.env['night.audit.folio'].search([
    #                 ('id', 'in', self.folio_ids.ids), ('booking_id', '!=', False), ('charged', '=', False)
    #             ], limit=limit)
    #             for line in folio_ids:
    #                 move = line.booking_id.move_id
    #                 if move:
    #                     move.write({'invoice_line_ids': self.prepare_invoice_lines(line.folio_id, line.folio_line_id)})
    #                 else:
    #                     self.create_invoice(line.folio_line_id)
    #                 line.charged = True
    #         if not remain:
    #             self.state = 'final'
    #             self.new_date = self.date + relativedelta(days=1)


    def state_exit_nightly_charge(self):
        self.ensure_one()
        print('callllllllllllllled state_exit_nightly_charge')

        if self.env.company.checkout_charge or self.env.company.related_hotel_id.unsettled_invoice:
            self.state = 'final'
            self.new_date = self.date + relativedelta(days=1)
            return

        remain = self.remaining_folios if self.enable_limit and self.remaining_folios else 0
        limit = self.limit if self.enable_limit else self.total_folios
        if not remain:
            self.state = 'final'
            self.new_date = self.date + relativedelta(days=1)
            print('hhhhhhhhhh not remain')
            return

        folio_lines = self.env['night.audit.folio'].search([
            ('id', 'in', self.folio_ids.ids),
            ('booking_id', '!=', False),
            ('charged', '=', False)
        ], limit=limit)

        booking_map = defaultdict(list)

        for line in folio_lines:
            booking = line.booking_id
            booking_map[booking.id].append(line)
        print('booking_map', booking_map)
        for booking_id, lines in booking_map.items():
            booking = lines[0].booking_id  # all lines share the same booking
            move = lines[0].booking_id.move_id
            print('booking', booking)
            print('move', move)

            invoice_lines = []
            for line in lines:
                invoice_lines += self.prepare_invoice_lines(line.folio_id, line.folio_line_id)
            print('invoice_lines before', invoice_lines)
            invoice_lines = self.grouped_invoice_lines(invoice_lines)
            if move:
                print('herrrrr exist move', move)
                for new_line in invoice_lines:
                    existing_lines = move.invoice_line_ids
                    print('new_line', new_line)
                    new_vals = new_line[2]
                    tax_ids = tuple(sorted(new_vals['tax_ids'][0][2])) if new_vals.get('tax_ids') else ()
                    key_new = (
                        new_vals['name'],
                        new_vals['account_id'],
                        tax_ids,
                        new_vals.get("pos_order_ref")
                    )
                    match = False
                    for line in existing_lines:
                        key_existing = (
                            line.name,
                            line.account_id.id,
                            tuple(sorted(line.tax_ids.ids)),
                            line.pos_order_ref
                        )
                        if key_existing == key_new:
                            print('match', key_existing, key_new)
                            print('match', line)
                            vals = {
                                'price_unit': line.price_unit + new_vals['price_unit'],
                                'product_id': line.product_id.id,
                                'name': line.name,
                                'quantity': line.quantity,
                                'source_booking_id': line.source_booking_id,
                                'tax_ids': line.tax_ids.ids,
                                'account_id': line.account_id.id,
                                'folio_line_id': line.folio_line_id.id,
                                'pos_order_ref': line.pos_order_ref,
                            }
                            move.write({
                                'invoice_line_ids': [
                                    (2, line.id),
                                    (0, 0, vals)
                                ]
                            })
                            match = True
                            break
                    if not match:
                        move.write({
                            'invoice_line_ids': [new_line]
                        })
            else:
                print('newwwwwwwww move')
                move_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': booking.company_booking_source.id if booking.company_booking_source else booking.partner_id.id,
                    'booking_id': booking.id,
                    'guest_id': booking.partner_id.id,
                    # 'narration': booking.conditions,
                    'invoice_user_id': self._uid,
                    'invoice_date': self.date,
                    'invoice_line_ids': invoice_lines
                }
                move = self.env['account.move'].with_context({'line_ids': False}).sudo().create(move_vals)
                booking.move_id = move.id

            # Mark lines as charged in batch
            lines_to_update = self.env['night.audit.folio'].browse([l.id for l in lines])
            lines_to_update.write({'charged': True})
            folio_line_ids = lines_to_update.mapped('folio_line_id')
            folio_line_ids.write({'is_invoiced': True})


    def create_invoice(self, line):
        """
        create draft invoice containing folio lines
        """
        self.ensure_one()
        # invoice_line_vals = []
        folio = line.folio_id
        booking = folio.booking_id
        invoice_line_vals = self.prepare_invoice_lines(folio, line)
        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': booking.company_booking_source.id if booking.company_booking_source else booking.partner_id.id,
            'booking_id': booking.id,
            'guest_id': booking.partner_id.id,
            # 'narration': booking.conditions,
            'invoice_user_id': self._uid,
            'invoice_date': self.date,
            'invoice_line_ids': invoice_line_vals
        }
        move = self.env['account.move'].with_context({'line_ids': False}).create(move_vals)
        booking.move_id = move.id

    def prepare_invoice_lines(self, folio, line):
        invoice_line_vals = []
        municipality_price = 0
        default_account = folio.room_id.product_id.categ_id.property_account_income_categ_id.id
        if folio.booking_line_id.price_include_tax:
            price_unit = line.amount
            if line.type == 'room_charge':
                vat_line = folio.line_ids.filtered(
                    lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax
                )
                municipality_line = folio.line_ids.filtered(
                    lambda
                        l: l.day == line.day and l.type == 'tax' and l.tax_type == 'municipality' and not l.is_service_tax
                )
            else:
                vat_line = folio.line_ids.filtered(
                    lambda l: l.tax_type == 'vat' and l.is_service_tax and l.related_line_id.id == line.id
                )
                municipality_line = folio.line_ids.filtered(
                    lambda
                        l: l.tax_type == 'municipality' and l.is_service_tax and l.related_line_id.id == line.id
                )
            if vat_line:
                price_unit += vat_line[0].amount
            if municipality_line:
                municipality_price = municipality_line[0].amount
        else:
            price_unit = line.amount
        invoice_line_vals.append((0, 0, {
            'product_id': folio.room_id.product_id.id,
            'name': line.particulars,
            'quantity': 1,
            'price_unit': price_unit,
            'source_booking_id': folio.booking_line_id.id,
            'tax_ids': [(6, 0, folio.booking_line_id.tax_id.filtered(lambda l: '15%' in (l.name or '').lower()).ids or [])],
            'account_id': line.get_account(line.type) or default_account,
            'folio_line_id': line.id,
            "pos_order_ref": line.pos_order_ref,
        }))
        if municipality_price:
            invoice_line_vals.append((0, 0, {
                'name': f"Municipality Tax",
                'quantity': 1,
                'price_unit': municipality_price,
                'source_booking_id': folio.booking_line_id.id,
                'tax_ids': [(6, 0, folio.booking_line_id.tax_id.filtered(lambda l: '15%' in (l.name or '').lower()).ids or [])],
                'account_id': line.get_account('tax') or default_account,
                'folio_line_id': line.id,
                "pos_order_ref": line.pos_order_ref,
            }))
        return invoice_line_vals

    def grouped_invoice_lines(self, invoice_lines):
        grouped = {}
        for command in invoice_lines:
            if command[0] != 0:
                continue
            vals = command[2]
            tax_ids = tuple(sorted(vals['tax_ids'][0][2])) if vals.get('tax_ids') else ()
            key = (
                vals['name'],
                vals['account_id'],
                tax_ids,  # extract tax IDs
                vals.get("pos_order_ref")
            )
            if key in grouped:
                grouped[key]['price_unit'] += vals['price_unit']
            else:
                grouped[key] = vals

        invoice_lines = [(0, 0, v) for v in grouped.values()]
        print('grouped invoice lines', invoice_lines)
        return invoice_lines

    def button_done(self):
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant')
        arrival = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival')
        arrived = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrived')
        stay_over = self.env.ref('hotel_booking.data_hotel_room_stay_status')
        duo_out = self.env.ref('hotel_booking.data_hotel_room_stay_status_duo_out')
        rooms = self.env['hotel.room'].search([('stay_state', 'in', [arrived.id, stay_over.id])])
        check_in_folios = self.env['booking.folio'].search([('state', '=', 'checked_in')])

        vacant_rooms = self.env['hotel.room'].search([('stay_state', 'in', [vacant.id])])
        confirmed_folios = self.env['booking.folio'].search([('state', 'in', ['draft', 'confirmed'])])

        for folio in confirmed_folios:
            if folio.room_id in vacant_rooms:
                if folio.check_in_date == self.new_date:
                    folio.room_id.stay_state = arrival.id

        for folio in check_in_folios:
            if folio.room_id in rooms:
                if folio.check_in_date < self.new_date == folio.check_out_date:
                    folio.room_id.stay_state = duo_out.id
                elif folio.check_in_date < self.new_date < folio.check_out_date:
                    folio.room_id.stay_state = stay_over.id

        for room in rooms:
            room.write({
                'state': self.env.ref('hotel_booking.hotel_room_status_dirty').id,
            })

        self.env.company.sudo().audit_date = self.new_date


class NightAuditDraftBooking(models.TransientModel):
    _inherit = 'night.audit.draft.booking'
    _order = 'id desc'

    folio_id = fields.Many2one('booking.folio')
    company_id = fields.Many2one('res.company', related='folio_id.company_id')
    room_type_id = fields.Many2one('room.type')
    room_id = fields.Many2one('hotel.room')
    # old fields
    check_out = fields.Datetime(related='folio_id.check_out')
    amount_total = fields.Monetary(string='Total', related='folio_id.price_total', store=True)
    paid_total = fields.Monetary(string='Deposit', related='folio_id.price_paid', compute=False, store=True)
    amount_balance = fields.Monetary(string='Balance', related='folio_id.price_due', compute=False, store=True)

    @api.onchange('action')
    def onchange_action(self):
        if self.action == 'check_in':
            available_room_ids = self.folio_id.get_available_rooms()
            draft_rooms = self.audit_id.draft_booking_ids.mapped('room_id').mapped('id')
            return {
                'domain': {
                    'room_id': [('id', 'in', list(set(available_room_ids) - set(draft_rooms)))]
                }
            }


class NightAuditCheckoutBooking(models.TransientModel):
    _inherit = 'night.audit.checkout.booking'
    _order = 'id desc'

    folio_id = fields.Many2one('booking.folio')
    room_type_id = fields.Many2one('room.type')
    room_id = fields.Many2one('hotel.room')
    # old fields
    check_in = fields.Datetime(related='folio_id.check_in')
    check_out = fields.Datetime(related='folio_id.check_out')
    amount_total = fields.Monetary(string='Total', related='folio_id.price_total', store=True)
    paid_total = fields.Monetary(string='Deposit', related='folio_id.price_paid', compute=False, store=True)
    amount_balance = fields.Monetary(string='Balance', related='folio_id.price_due', compute=False, store=True)


class NightAuditRoomState(models.TransientModel):
    _inherit = 'night.audit.room.state'
    _order = 'id desc'

    folio_id = fields.Many2one('booking.folio')
    room_type_id = fields.Many2one('room.type')
    room_id = fields.Many2one('hotel.room', related='folio_id.room_id', store=True)
    # old fields
    check_in = fields.Datetime(related='folio_id.check_in', store=True)
    check_out = fields.Datetime(related='folio_id.check_out', store=True)
    amount_total = fields.Monetary(string='Total', related='folio_id.price_total', store=True)
    paid_total = fields.Monetary(string='Deposit', related='folio_id.price_paid', compute=False, store=True)
    amount_balance = fields.Monetary(string='Balance', related='folio_id.price_due', compute=False, store=True)


class NightAuditFolio(models.TransientModel):
    _inherit = 'night.audit.folio'
    _order = 'id desc'

    # old fields
    room_id = fields.Many2one('hotel.room', related='folio_id.room_id', store=True)
    amount_total = fields.Monetary(string='Total', related='folio_id.price_total', store=True)
    paid_total = fields.Monetary(string='Deposit', related='folio_id.price_paid', compute=False, store=True)
    amount_balance = fields.Monetary(string='Balance', related='folio_id.price_due', compute=False, store=True)
    charged = fields.Boolean()
