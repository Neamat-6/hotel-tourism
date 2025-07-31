from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class FlightSchedule(models.Model):
    _name = 'flight.schedule'
    _rec_name = 'name'


    partner_id = fields.Many2one('res.partner', string="Supplier", required=True, domain=[('is_company', '=', True)])
    flight_date = fields.Date("Flight Date")
    airport = fields.Char("Airport")
    arrival_flight_no = fields.Char("Flight Number")
    departure_flight_no = fields.Char("Flight Number")
    date_from = fields.Datetime("Date From")
    date_to = fields.Datetime("Date To")
    arrival_hall_no = fields.Char("Arrival Hall No.")
    departure_hall_no = fields.Char("Departure Hall No.")
    pilgrims_no = fields.Integer("Pilgrims No.")
    booked_no = fields.Integer("Booked No.", compute='_compute_booked_no')
    available_no = fields.Integer("Available No.", compute='_compute_available_no')
    arrival_date = fields.Datetime("Arrival Date")
    departure_date = fields.Datetime("Departure Date")
    flight_type = fields.Selection([('arrival', 'Arrival'), ('departure', 'Departure')], string='Flight Type')
    arrival_airport_id = fields.Many2one('airport.management', "Arrival Airport")
    arrival_airport_dep_id = fields.Many2one('airport.management', "Arrival Airport")
    departure_airport_id = fields.Many2one('airport.management', "Departure Airport")
    departure_airport_arrival_id = fields.Many2one('airport.management', "Departure Airport")
    unit_price = fields.Monetary("Unit Price")
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirm', 'Confirm')], required=False, default='draft')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    purchase_id = fields.Many2one('purchase.order')
    name = fields.Char()
    contract_type = fields.Selection(selection=[('B2B', 'B2B'), ('B2C', 'B2C'), ('B2G', 'B2G')])
    expiry_date = fields.Date("Expiry Date")
    is_expired = fields.Boolean("Is Expired", default=False)
    partner_count = fields.Integer(compute='_compute_booked_no')

    _sql_constraints = [('arrival_departure_date', 'check(arrival_date < departure_date)', 'Departure Date must be greater than Arrival Date!')]

    @api.model
    def _cron_update_contract_expiry(self):
        """This method is called daily via a scheduled action"""
        packages = self.search([])
        today = fields.Date.today()
        for record in packages:
            record.is_expired = bool(record.expiry_date and record.expiry_date < today)


    @api.constrains('pilgrims_no', 'booked_no')
    def _check_booked_no(self):
        for record in self:
            if record.booked_no > record.pilgrims_no:
                raise ValidationError('Booked No. must be less than or equal to Pilgrims No.!')

    def action_create_purchase_order(self):
        product = self.env['product.product'].sudo().search([('name', '=', 'Flight Product')], limit=1)
        if not product:
            product = self.env['product.product'].sudo().create({
                'name': 'Flight Product',
                'type': 'service',
                'categ_id': self.env.ref('product.product_category_all').id,
                'list_price': 0.0,
                'standard_price': 0.0,
            })
        product_id = product.id
        purchase_order = self.env['purchase.order'].sudo().create({
            'partner_id': self.partner_id.id,
            'date_order': fields.Datetime.now(),
            'order_line': [(0, 0, {
                'name': f'Flight Contract: {self.name}',
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
            flight_schedule_pilgrim = self.env['res.partner'].search([('flight_schedule_id', '=', record.id)])
            flight_contract_booking = self.env['contract.booking'].search([('flight_contract', '=', record.id), ('state', 'in', ['hotel_confirm', 'confirmed'])])
            if flight_contract_booking:
                booked_count = sum(flight_contract_booking.mapped('flight_count'))
            record.booked_no = len(flight_schedule_pilgrim) + booked_count
            record.partner_count = len(flight_schedule_pilgrim)

    def action_view_pilgrims(self):
        return {
            'name': _('Pilgrims'),
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'domain': [('flight_schedule_id', '=', self.id)],
        }


class FlightScheduleLine(models.Model):
    _name = 'flight.schedule.line'
    _rec_name = 'flight_contract_id'

    flight_contract_id = fields.Many2one('flight.schedule', string="Flight Contract", domain="[('is_expired', '=', False)]")
    available_no = fields.Integer(string="Available No.", related='flight_contract_id.available_no')
    booked_no = fields.Integer(string="Booked No.", related='flight_contract_id.booked_no')
    sale_price = fields.Float(string="Sale Price")
    purchase_currency_id = fields.Many2one(
        'res.currency',
        related='flight_contract_id.purchase_id.currency_id',
        string='Purchase Currency',
        store=True,
        readonly=True
    )
    purchase_price = fields.Monetary(string="Purchase Price",
                                     related='flight_contract_id.purchase_id.amount_total',
                                     currency_field='purchase_currency_id')
    package_id = fields.Many2one('booking.package', string="Package", ondelete='cascade')

    _sql_constraints = [('package_flight_contract_uniq', 'unique(flight_contract_id, package_id)', 'Flight Contract must be unique per Package!')]
