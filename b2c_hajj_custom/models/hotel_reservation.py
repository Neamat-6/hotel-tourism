from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'
    hotel_reservation_id = fields.Many2one('hotel.reservation', string='Hotel Reservation')
    hotel_reservation_ref = fields.Char(string='Hotel Reservation Ref.')

class RoomReservation(models.Model):
    _name = 'room.reservation'

    name = fields.Char(required=True)


class RoomView(models.Model):
    _name = 'room.view'

    name = fields.Char(required=True)

class MealReservation(models.Model):
    _name = 'meal.reservation'

    name = fields.Char(required=True)


class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _inherit = ["mail.thread", 'portal.mixin']
    _description = 'Hotel Reservation'
    _rec_name = 'booking_ref'

    customer_id = fields.Many2one('res.partner', string='Customer')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company')
    state= fields.Selection([('draft', 'Tentative Confirmation'),('hotel_confirm', 'Confirmed Waiting Payment'),('confirmed', 'Confirmed'),('cancelled', 'Cancelled')], default='draft')
    notes = fields.Text("Notes")
    booking_ref = fields.Char("Booking Ref.")
    move_id = fields.Many2one('account.move', copy=False)
    bill_id = fields.Many2one('account.move', copy=False)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
    line_ids = fields.One2many('hotel.reservation.line', 'reservation_id', string='Lines')
    total_amount = fields.Float('Total Amount', compute='get_total_amount', store=True)
    subtotal_amount = fields.Float('Subtotal Amount', compute='get_total_amount', store=True)
    tax_amount = fields.Float('Tax Amount', compute='get_total_amount', store=True)
    line_count = fields.Integer(compute='calc_lines_count')

    @api.depends('line_ids')
    def calc_lines_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.depends('line_ids.total_amount', 'line_ids.tax_amount', 'line_ids.subtotal_amount')
    def get_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped('total_amount'))
            rec.tax_amount = sum(rec.line_ids.mapped('tax_amount'))
            rec.subtotal_amount = sum(rec.line_ids.mapped('subtotal_amount'))

    def action_reset_to_draft(self):
        for rec in self:
            rec.move_id.button_draft()
            rec.bill_id.button_draft()
            rec.state = 'draft'

    def action_cancel(self):
        for rec in self:
            rec.move_id.button_cancel()
            rec.bill_id.button_cancel()
            rec.state = 'cancelled'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Cannot delete a record which is in state \'%s\'.') % (rec.state,))
            if rec.move_id:
                rec.move_id.button_cancel()
                rec.move_id.unlink()
                rec.move_id = False
            if rec.bill_id:
                rec.bill_id.button_cancel()
                rec.bill_id.unlink()
                rec.bill_id = False
        return super(HotelReservation, self).unlink()


    def action_open_invoice(self):
        self.ensure_one()
        if self.move_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Invoice'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': self.move_id.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window_close',
            }

    def action_open_bill(self):
        self.ensure_one()
        if self.bill_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Bill'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': self.bill_id.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window_close',
            }

    def action_confirm(self):
        for rec in self:
            if rec.move_id:
                # if rec.move_id.payment_state != 'paid':
                if rec.move_id.amount_residual != 0:
                    raise UserError("The linked invoice must be fully paid before confirming.")
                rec.state = 'confirmed'
            else:
                raise UserError("Must create invoice first")

    def action_create_invoices(self):
        """Action to create both customer invoice and vendor bill"""
        self.ensure_one()
        self.create_customer_invoice()
        # bill = self.create_vendor_bill()
        self.state = 'hotel_confirm'
        return True

    def create_customer_invoice(self):
        self.ensure_one()
        if not self.customer_id:
            raise UserError(_("Please select a customer first."))
        if self.move_id:
            if self.move_id.state == 'draft':
                self.move_id.unlink()
            else:
                raise UserError(_("An invoice already exists and is in %s state." % self.move_id.state))

        invoice_vals = self._prepare_invoice_vals(
            self.customer_id.id,
            'out_invoice',
            self.line_ids,
        )
        move = self.env['account.move'].with_context({'line_ids': False, }).with_company(self.company_id).create(invoice_vals)
        self.move_id = move.id
        move.action_post()
        return move

    def _prepare_invoice_vals(self, partner_id, move_type, line_ids):
        """Prepare invoice/bill values"""
        invoice_line_ids = []
        for line in line_ids:
            product_id = self.env['product.product'].sudo().search([('name', '=', line.room_id.name)])
            if not product_id:
                product_id = self.env['product.product'].sudo().create({
                    'name': line.room_id.name,
                    'type': 'service',
                })
            invoice_line_ids.append((0, 0, {
                "product_id":product_id.id,
                "quantity": line.total_nights * line.count,
                "price_unit": line.price if move_type == 'out_invoice' else line.cost,
                "tax_ids": line.tax_id if move_type == 'out_invoice' else line.purchase_tax_id,
            }))

        return {
            'hotel_reservation_ref': self.booking_ref,
            'move_type': move_type,
            'partner_id': partner_id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_user_id': self._uid,
            'hotel_reservation_id': self.id,
            'company_id': self.company_id.id,
            "currency_id": self.currency_id.id,
            'invoice_line_ids': invoice_line_ids,
        }

    def create_vendor_bill(self):
        self.ensure_one()
        if not self.vendor_id:
            raise UserError(_("Please select a vendor first."))
        if self.bill_id:
            if self.bill_id.state == 'draft':
                self.bill_id.unlink()
            else:
                raise UserError(_("A bill already exists and is in %s state." % self.bill_id.state))

        bill_vals = self._prepare_invoice_vals(
            self.vendor_id.id,
            'in_invoice',
            self.line_ids,
        )

        # move = self.env['account.move'].create(bill_vals)
        move = self.env['account.move'].with_context({'line_ids': False, }).with_company(
            self.company_id).create(bill_vals)

        self.bill_id = move.id
        move.action_post()
        return True


class HotelReservationLine(models.Model):
    _name = 'hotel.reservation.line'
    _description = 'Hotel Reservation Line'

    reservation_id = fields.Many2one('hotel.reservation', required=True, ondelete="cascade")
    hotel_id = fields.Many2one('actual.hotel', required=True)
    room_id = fields.Many2one('room.reservation', string='Room', required=True)
    room_view_id = fields.Many2one('room.view', string="Room View")
    meal_id = fields.Many2many('meal.reservation', string="Meal")
    check_in = fields.Date(string='Check In', default=fields.Date.today(), required=True)
    check_out = fields.Date(string='Check Out', default=fields.Date.today(), required=True)
    total_nights = fields.Integer(' Total Nights', compute='_compute_total_days', store=True)
    price = fields.Float('Sales Price')
    cost = fields.Float('Cost Price')
    company_id = fields.Many2one('res.company', string='Company', related='reservation_id.company_id')
    tax_id = fields.Many2one('account.tax', string='Tax', domain=[('type_tax_use', '=', 'sale'),('company_id', '=', company_id)])
    purchase_tax_id = fields.Many2one('account.tax', string='Purchase Tax', domain=[('type_tax_use', '=', 'purchase'),('company_id', '=', company_id)])
    count = fields.Integer('Number Of Room', default=1)
    number_of_adults = fields.Integer(string='Adults', default=1, )
    number_of_children = fields.Integer(string='Children', default=0, )

    # actual_check_in = fields.Datetime(string="Actual Check-In", compute="compute_actual_check_in_out")
    # actual_check_out = fields.Datetime(string="Actual Check-Out", compute="compute_actual_check_in_out")
    # actual_number_of_days = fields.Integer(string='Actual Days', compute="compute_actual_check_in_out")
    total_amount = fields.Float('Total', compute='get_tax_amount', store=True)
    tax_amount = fields.Float('Tax Amount', compute='get_tax_amount', store=True)
    subtotal_amount = fields.Float('Tax Amount', compute='get_subtotal_amount', store=True)
    currency_id = fields.Many2one('res.currency',related='reservation_id.currency_id')


    @api.constrains('check_in', 'check_out')
    def check_check_in_out_date(self):
        if self.check_out <= self.check_in:
            raise UserError(_("Check out date must be greater than check in date"))

    @api.depends('tax_id', 'subtotal_amount')
    def get_tax_amount(self):
        for rec in self:
            rec.tax_amount = 0.0
            if rec.tax_id:
                taxes = rec.tax_id.compute_all(rec.total_amount, currency=rec.currency_id)
                rec.tax_amount = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                rec.total_amount = taxes.get('total_included')
            else:
                rec.tax_amount = 0.0
                rec.total_amount = rec.subtotal_amount

    @api.depends('count', 'price', 'total_nights')
    def get_subtotal_amount(self):
        for rec in self:
            rec.subtotal_amount = rec.count * rec.price * rec.total_nights


    @api.depends('check_in', 'check_out')
    def _compute_total_days(self):
        for rec in self:
            rec.total_nights = 0
            if rec.check_out and rec.check_in:
                delta = (rec.check_out - rec.check_in).days
                rec.total_nights = delta if delta > 0 else 0
