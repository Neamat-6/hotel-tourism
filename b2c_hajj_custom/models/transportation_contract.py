from odoo import fields, models, api
from odoo.exceptions import ValidationError


class TransportationContract(models.Model):
    _name = 'transportation.contract'
    _rec_name = 'transportation_contract_no'

    transportation_company = fields.Many2one('res.partner', domain=[('is_transportation_company', '=', True)])
    no_buses = fields.Char('No. of Buses')
    transportation_contract_no = fields.Char("Transportation Contract")
    location_lines = fields.One2many('transportation.location.line', 'contract_id')
    pilgrims_no = fields.Integer(string='Pilgrims NO.')
    booked_no = fields.Integer(string='Booked NO.', compute='_compute_booked_no')
    available_no = fields.Integer(string='Available NO.', compute='_compute_available_no')
    cost_price = fields.Float(string='Cost Price')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, readonly=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True, copy=False)
    expiry_date = fields.Date("Expiry Date")
    is_expired = fields.Boolean("Is Expired", default=False)

    @api.model
    def _cron_update_contract_expiry(self):
        """This method is called daily via a scheduled action"""
        contracts = self.search([])
        today = fields.Date.today()
        for record in contracts:
            record.is_expired = bool(record.expiry_date and record.expiry_date < today)


    def button_create_purchase_order(self):
        for rec in self:
            if not all([rec.transportation_company, rec.transportation_contract_no, rec.pilgrims_no, rec.cost_price]):
                raise ValidationError('Please fill in all required fields before creating a purchase order.')
            po_vals = {
                'partner_id': rec.transportation_company.id,
                'company_id': rec.company_id.id,
                'origin': rec.transportation_contract_no,
                'order_line': [],
            }

            product = self.env['product.product'].sudo().search([('name', '=', 'Transportation Product')], limit=1)
            if not product:
                product = self.env['product.product'].sudo().create({
                    'name': 'Transportation Product',
                    'type': 'service',
                    'categ_id': self.env.ref('product.product_category_all').id,
                    'list_price': 0.0,
                    'standard_price': 0.0,
                })
            product_id = product.id
            po_vals['order_line'].append((0, 0, {
                'product_id': product_id,
                'name': f"{rec.transportation_contract_no}",
                'product_qty': rec.pilgrims_no,
                'price_unit': rec.cost_price,
                'date_planned': fields.Date.today(),
                'company_id': self.company_id.id,
            }))

            purchase_order = self.env['purchase.order'].create(po_vals)
            rec.purchase_order_id = purchase_order.id

    @api.constrains('pilgrims_no', 'booked_no')
    def _check_booked_no(self):
        for record in self:
            if record.booked_no > record.pilgrims_no:
                raise ValidationError('Booked No. must be less than or equal to Pilgrims No.!')

    @api.depends('pilgrims_no', 'booked_no')
    def _compute_available_no(self):
        for record in self:
            if record.pilgrims_no > 0:
                record.available_no = record.pilgrims_no - record.booked_no
            else:
                record.available_no = 0

    def _compute_booked_no(self):
        for record in self:
            trans_contract_pilgrim = self.env['res.partner'].search([('transportation_contract_ids', 'in', record.id)])
            record.booked_no = len(trans_contract_pilgrim)



