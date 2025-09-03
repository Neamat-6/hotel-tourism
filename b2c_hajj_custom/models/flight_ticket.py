from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'
    flight_ticket_id = fields.Many2one('flight.ticket', string='Flight Ticket')
    ticket_booking_ref = fields.Char(string='Ticket Booking Ref.')


class FlightCompany(models.Model):
    _name = 'flight.company'

    name = fields.Char(string='Name', required=True)



class FlightTicket(models.Model):
    _name = 'flight.ticket'
    _description = 'Flight Ticket'
    _rec_name = 'booking_ref'
    _inherit = ["mail.thread", 'portal.mixin']

    customer_id = fields.Many2one('res.partner', string='Customer')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    no_ticket = fields.Integer(string='No Ticket')
    sale_price = fields.Float(string='Sale Price')
    purchase_price = fields.Float(string='Purchase Price')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company')
    state= fields.Selection([('draft', 'Tentative Confirmation'),('hotel_confirm', 'Confirmed Waiting Payment'),('confirmed', 'Confirmed'),('cancelled', 'Cancelled')], default='draft')
    arrival_flight_no = fields.Char("Flight Number")
    departure_flight_no = fields.Char("Flight Number")
    arrival_date = fields.Datetime("Arrival Date")
    departure_date = fields.Datetime("Departure Date")
    departure_airport_arrival_id = fields.Many2one('airport.management', "Departure Airport")
    arrival_airport_id = fields.Many2one('airport.management', "Arrival Airport")
    arrival_hall_no = fields.Char("Arrival Hall No.")
    departure_airport_id = fields.Many2one('airport.management', "Departure Airport")
    arrival_airport_dep_id = fields.Many2one('airport.management', "Arrival Airport")
    departure_hall_no = fields.Char("Departure Hall No.")
    move_id = fields.Many2one('account.move', copy=False)
    bill_id = fields.Many2one('account.move', copy=False)
    notes = fields.Text("Notes")
    booking_ref = fields.Char("Booking Ref.")
    flight_company_id = fields.Many2one('flight.company', "Flight Company")
    flight_type = fields.Selection([('national', 'National'),('international','International')])
    direction = fields.Selection([('arrival', 'Arrival'),('departure','Departure'), ('arrival-dep', 'Arrival and Departure'), ('multi_direction','Multiple directions')])
    profit = fields.Float(string='Profit', compute='_compute_profit', store=True)
    seat_type = fields.Selection([('adult', 'Adult'),('child','Child'),('baby','Baby')])
    ticket_type = fields.Selection([('issue', 'Issue'),('reissue','Reissue'),('refund','Refund'), ('re_validate','ReValidate')])

    @api.depends('sale_price', 'purchase_price', 'no_ticket')
    def _compute_profit(self):
        for rec in self:
            rec.profit = (rec.sale_price - rec.purchase_price) * rec.no_ticket


    def action_confirm(self):
        for rec in self:
            if rec.move_id:
                # if rec.move_id.payment_state != 'paid':
                if rec.move_id.amount_residual != 0:
                    raise UserError("The linked invoice must be fully paid before confirming.")
                rec.state = 'confirmed'
            else:
                raise UserError("Must create invoice first")

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
        return super(FlightTicket, self).unlink()

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

    def _prepare_invoice_vals(self, partner_id, move_type, price_unit):
        """Prepare invoice/bill values"""
        product = self.env.ref('b2c_hajj_custom.flight_ticket', False)
        print('product', product)
        if not product:
            raise ValidationError(_("Flight Ticket product not found. Please create a product with XML ID 'b2c_hajj_custom.product_flight_ticket'"))
            
        return {
            'ticket_booking_ref': self.booking_ref,
            'move_type': move_type,
            'partner_id': partner_id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_user_id': self._uid,
            'flight_ticket_id': self.id,
            'company_id': self.company_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': self.no_ticket or 1,
                'price_unit': price_unit,
                # 'account_id': product.property_account_income_id.id if move_type == 'out_invoice' else product.property_account_expense_id.id,
            })]
        }

    def create_customer_invoice(self):
        """Create customer invoice for the flight ticket"""
        self.ensure_one()
        if not self.customer_id:
            raise UserError(_("Please select a customer first."))
            
        if not self.sale_price:
            raise UserError(_("Please set the sale price first."))
            
        if self.move_id:
            if self.move_id.state == 'draft':
                self.move_id.unlink()
            else:
                raise UserError(_("An invoice already exists and is in %s state." % self.move_id.state))
        
        invoice_vals = self._prepare_invoice_vals(
            self.customer_id.id, 
            'out_invoice',
            self.sale_price,
        )
        
        # move = self.env['account.move'].create(invoice_vals)
        move = self.env['account.move'].with_context({'line_ids': False, }).with_company(self.company_id).create(invoice_vals)
        self.move_id = move.id
        move.action_post()
        return move

    def create_vendor_bill(self):
        """Create vendor bill for the flight ticket"""
        self.ensure_one()
        if not self.vendor_id:
            raise UserError(_("Please select a vendor first."))
            
        if not self.purchase_price:
            raise UserError(_("Please set the purchase price first."))
            
        if self.bill_id:
            if self.bill_id.state == 'draft':
                self.bill_id.unlink()
            else:
                raise UserError(_("A bill already exists and is in %s state." % self.bill_id.state))
        
        bill_vals = self._prepare_invoice_vals(
            self.vendor_id.id,
            'in_invoice',
            self.purchase_price,
        )
        
        # move = self.env['account.move'].create(bill_vals)
        move = self.env['account.move'].with_context({'line_ids': False, }).with_company(self.company_id).create(bill_vals)

        self.bill_id = move.id
        move.action_post()
        return {
            'name': _('Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', '=', move.id)],
            'target': 'current',
        }
        # return move

    def action_create_invoices(self):
        """Action to create both customer invoice and vendor bill"""
        self.ensure_one()
        invoice = self.create_customer_invoice()
        # bill = self.create_vendor_bill()
        self.state = 'hotel_confirm'
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', '=', invoice.id)],
            'target': 'current',
        }

    def flight_ticket(self):
        for rec in self:
            if not rec.total_cost:
                raise UserError(_("can not create invoice with zero amount"))
            if not rec.move_id:
                rec.create_invoice()
            else:
                print('hhhhhhhhhhhhhhhhhhhhhhhh')
                rec.update_invoice()
            rec.state = 'hotel_confirm'