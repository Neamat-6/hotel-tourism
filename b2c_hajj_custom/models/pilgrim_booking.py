from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    pilgrim_booking_id = fields.Many2one('pilgrim.booking')


class PilgrimBooking(models.Model):
    _name = 'pilgrim.booking'
    _rec_name = 'partner_id'
    _inherit = ["mail.thread", 'portal.mixin']

    source = fields.Selection([('person','Direct'), ('company','Company')],required=True)
    partner_id = fields.Many2one('res.partner',required=True)
    package_id = fields.Many2one('booking.package', required=True, domain="[('package_closed', '=', False)]")
    pilgrim_count = fields.Integer()
    pilgrim_cost = fields.Float(string="sales Price")
    total_cost = fields.Float(compute='compute_total_cost', store=True)
    room_type = fields.Selection(selection=[('2', '2'), ('3', '3'), ('4', '4')])
    line_ids = fields.One2many('pilgrim.booking.line', 'book_id')
    state= fields.Selection([('draft', 'Tentative Confirmation'),('hotel_confirm', 'Confirmed Waiting Payment'),('confirmed', 'Confirmed'),('cancelled', 'Cancelled')], default='draft')
    move_id = fields.Many2one('account.move', copy=False)

    @api.constrains('line_ids', 'pilgrim_count', 'source')
    def _check_line_count(self):
        for rec in self:
            if rec.pilgrim_count:
                if rec.source == 'company':
                    if len(rec.line_ids) != rec.pilgrim_count:
                        raise UserError(_("The number of pilgrims must match the number of pilgrims lines"))
                if len(rec.line_ids) != rec.pilgrim_count - 1:
                    raise UserError(_("The number of pilgrims must match the number of pilgrims lines minus one."))

    @api.onchange('source')
    def _onchange_source(self):
        self.partner_id = False
        domain = []
        if self.source == 'person':
            domain = [('is_company', '=', False)]
        elif self.source == 'company':
            domain = [('is_company', '=', True)]

        return {
            'domain': {
                'partner_id': domain
            }
        }

    @api.depends('pilgrim_count', 'pilgrim_cost')
    def compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.pilgrim_count * rec.pilgrim_cost


    def create_invoice(self):
        self.ensure_one()
        tax_ids = self.env.company.hotel_default_tax_ids.ids
        invoice_line_vals = [(0, 0, {
                # 'product_id': line.room_id.product_id.id,
                'name': self.package_id.package_code,
                'quantity': self.pilgrim_count,
                'price_unit': self.pilgrim_cost,
                # 'tax_ids': line.tax_id,
                # 'account_id': hotel_hotel_obj.account_journal_id.default_account_id.id
            })]

        # for rec in self.line_ids:
        #     if rec.check_dir:
        #         journal_id = self.env['hotel.hotel'].sudo().search([('partner_id', '=', rec.vendor_id.id)],
        #                                                            limit=1).account_journal_id.id
        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'pilgrim_booking_id': self.id,
            # 'journal_id': journal_id,
            'invoice_user_id': self._uid,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_line_vals
        }
        move = self.env['account.move'].with_context({'line_ids': False}).create(move_vals)
        move.action_post()
        print('mmmmmmmmmove', move)
        self.move_id = move.id

    def update_invoice(self):
        print('callllllllllllllllllled')
        self.move_id.line_ids.unlink()
        self.move_id.invoice_line_ids.unlink()
        print('after delete', self.move_id)
        income_account = self.env['account.account'].search([
            ('user_type_id.type', '=', 'income'),
            ('deprecated', '=', False),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        print('income_account', income_account)
        invoice_line_vals = [(0, 0, {
                # 'product_id': line.room_id.product_id.id,
                'name': self.package_id.package_code,
                'quantity': self.pilgrim_count,
                'price_unit': self.pilgrim_cost,
                'account_id': income_account.id,
                # 'tax_ids': line.tax_id,
                # 'account_id': hotel_hotel_obj.account_journal_id.default_account_id.id
            })]
        self.move_id.write({
            'partner_id': self.partner_id.id,
            'invoice_line_ids': invoice_line_vals
        })
        self.move_id._recompute_dynamic_lines(recompute_all_taxes=True)
        self.move_id.action_post()

    def create_booking(self):
        for rec in self:
            if not rec.total_cost:
                raise UserError(_("can not create invoice with zero amount"))
            if not rec.move_id:
                rec.create_invoice()
            else:
                print('hhhhhhhhhhhhhhhhhhhhhhhh')
                rec.update_invoice()
            if rec.source == 'person':
                rec.partner_id.write({'package_id': rec.package_id,
                                      'makkah_room_type': rec.room_type,
                                       'madinah_room_type': rec.room_type,
                                       'hotel_room_type': rec.room_type})
            for line in rec.line_ids:
                vals = line.get_pilgrim_data()
                if line.partner_id:
                    line.partner_id.sudo().write(vals)
                else:
                    pilgrim = self.env['res.partner'].sudo().create(vals)
                    line.write({'partner_id': pilgrim.id})
            rec.state = 'hotel_confirm'

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
            if rec.source == 'person':
                rec.partner_id.sudo().update({
                    'package_id': False,
                })
            for line in rec.line_ids:
                line.partner_id.write({
                    'package_id': False,
                })
            rec.move_id.button_draft()
            rec.state = 'draft'


    def action_cancel(self):
        for rec in self:
            if rec.source == 'person':
                rec.partner_id.sudo().update({
                    'package_id': False,
                })
            for line in rec.line_ids:
                line.partner_id.write({
                    'package_id': False,
                })
            rec.move_id.button_cancel()
            rec.state = 'cancelled'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Cannot delete a record which is in state \'%s\'.') % (rec.state,))
        return super(PilgrimBooking, self).unlink()

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




class PilgrimBookingLine(models.Model):
    _name = 'pilgrim.booking.line'

    name = fields.Char()
    main_member_id = fields.Many2one('res.partner')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    pilgrim_type = fields.Selection(selection=[
        ('main', 'Main'), ('member', 'Family Member')
    ])
    book_id = fields.Many2one('pilgrim.booking', ondelete='cascade')
    partner_id = fields.Many2one('res.partner')

    @api.onchange('pilgrim_type')
    def onchange_pilgrim_type(self):
        for rec in self:
            if rec.pilgrim_type == 'member':
                if rec.book_id.source == 'person':
                    rec.main_member_id = rec.book_id.partner_id.id
            else:
                rec.main_member_id = False

    def get_pilgrim_data(self):
        return {
            'name': self.name,
            'gender': self.gender,
            'pilgrim_type': self.pilgrim_type,
            'main_member_id': self.main_member_id.id if self.main_member_id else None,
            'package_id': self.book_id.package_id.id,
            'makkah_room_type': self.book_id.room_type,
            'madinah_room_type': self.book_id.room_type,
            'hotel_room_type': self.book_id.room_type,
        }