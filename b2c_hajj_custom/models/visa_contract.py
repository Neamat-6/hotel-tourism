from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class VisaContract(models.Model):
    _name = 'visa.contract'
    _description = 'Visa Contract'

    name = fields.Char()
    partner_id = fields.Many2one('res.partner', string="Supplier", required=True, domain=[('is_company', '=', True)])
    unit_price = fields.Monetary("Unit Price")
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirm', 'Confirm')], required=False, default='draft')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
    purchase_id = fields.Many2one('purchase.order')
    contract_type = fields.Selection(selection=[('Visa', 'visa'), ('Barcode', 'barcode')])
    expiry_date = fields.Date("Expiry Date")
    is_expired = fields.Boolean("Is Expired", default=False)
    pilgrims_no = fields.Integer("Pilgrims No.")
    booked_no = fields.Integer("Booked No.", compute='_compute_booked_no')
    available_no = fields.Integer("Available No.", compute='_compute_available_no')
    partner_count = fields.Integer(compute='_compute_booked_no')
    total = fields.Monetary(string="Total", compute="_compute_total", store=True)

    @api.depends('pilgrims_no', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.pilgrims_no * rec.unit_price

    @api.model
    def _cron_update_contract_expiry(self):
        """This method is called daily via a scheduled action"""
        contracts = self.search([])
        today = fields.Date.today()
        for record in contracts:
            record.is_expired = bool(record.expiry_date and record.expiry_date < today)


    @api.constrains('pilgrims_no', 'booked_no')
    def _check_booked_no(self):
        for record in self:
            if record.booked_no > record.pilgrims_no:
                raise ValidationError('Booked No. must be less than or equal to Pilgrims No.!')

    def action_create_purchase_order(self):
        product = self.env['product.product'].sudo().search([('name', '=', 'Visa Product')], limit=1)
        if not product:
            product = self.env['product.product'].sudo().create({
                'name': 'Visa Product',
                'type': 'service',
                'categ_id': self.env.ref('product.product_category_all').id,
                'list_price': 0.0,
                'standard_price': 0.0,
            })
        product_id = product.id
        purchase_order = self.env['purchase.order'].sudo().create({
            'partner_id': self.partner_id.id,
            'date_order': fields.Datetime.now(),
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'order_line': [(0, 0, {
                'name': f'Visa Contract: {self.name}',
                'product_id': product_id,
                'product_qty': self.pilgrims_no,
                'price_unit': self.unit_price,
                'date_planned': fields.Datetime.now(),
                'company_id': self.env.company.id,
            })],
        })
        self.state = 'confirm'
        self.purchase_id = purchase_order.id

    def action_reset_to_draft(self):
        for record in self:
            if record.purchase_id:
                record.purchase_id.button_cancel()
                record.purchase_id.unlink()
                record.purchase_id = False

            record.state = 'draft'

    @api.depends('pilgrims_no', 'booked_no')
    def _compute_available_no(self):
        for record in self:
            if record.pilgrims_no > 0:
                record.available_no = record.pilgrims_no - record.booked_no
            else:
                record.available_no = 0

    def _compute_booked_no(self):
        for record in self:
            booked_count = 0
            visa_contract_pilgrim = self.env['res.partner'].search([('visa_contract_id', '=', record.id)])
            visa_contract_booking = self.env['contract.booking'].search([('visa_contract', '=', record.id), ('state', 'in', ['hotel_confirm', 'confirmed'])])
            if visa_contract_booking:
                booked_count = sum(visa_contract_booking.mapped('visa_count'))
            record.booked_no = len(visa_contract_pilgrim) + booked_count
            record.partner_count = len(visa_contract_pilgrim)

    def action_view_pilgrims(self):
        return {
            'name': _('Pilgrims'),
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'domain': [('visa_contract_id', '=', self.id)],
        }


class VisaContractLine(models.Model):
    _name = 'visa.contract.line'
    _rec_name = 'visa_contract_id'

    visa_contract_id = fields.Many2one('visa.contract', string="Visa Contract", domain="[('is_expired', '=', False)]")
    available_no = fields.Integer(string="Available No.", related='visa_contract_id.available_no')
    booked_no = fields.Integer(string="Booked No.", related='visa_contract_id.booked_no')
    sale_price = fields.Float(string="Sale Price")
    purchase_currency_id = fields.Many2one(
        'res.currency',
        related='visa_contract_id.purchase_id.currency_id',
        string='Purchase Currency',
        store=True,
        readonly=True
    )
    purchase_price = fields.Monetary(string="Purchase Price",
                                     related='visa_contract_id.purchase_id.amount_total',
                                     currency_field='purchase_currency_id')
    package_id = fields.Many2one('booking.package', string="Package", ondelete='cascade')

    _sql_constraints = [('package_visa_contract_uniq', 'unique(visa_contract_id, package_id)', 'Visa Contract must be unique per Package!')]
