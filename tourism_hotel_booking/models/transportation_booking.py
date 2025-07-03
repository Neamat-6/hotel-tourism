from odoo import api, fields, models
from datetime import datetime


class TransportationBooking(models.Model):
    _name = 'transportation.booking'
    product_id = fields.Many2one('product.product', 'Transportation')
    bus_type = fields.Char('Bus Type')
    bus_type_id = fields.Many2one('bus.type', string='Bus Type')
    no_of_bus = fields.Integer('No Of Bus')
    no_of_passengers = fields.Integer('No Of Passengers')
    departure_date = fields.Date("Departure")
    return_date = fields.Date("Return")
    days = fields.Integer("Days", compute='calc_days')
    cost_price = fields.Float(string="Cost Price", store=True)
    sell_price = fields.Float(string="Sell Price", store=True)

    customer_package_id = fields.Many2one('hotel.transport.package', string="Customer Package", domain="[('id', 'in', customer_available_package_ids)]")

    customer_available_package_ids = fields.Many2many('hotel.transport.package', compute='_compute_available_packages', store=True)

    tax_ids = fields.Many2many('account.tax', string='Taxes', relation='tax_ids')
    purchase_tax_ids = fields.Many2many('account.tax', string='Purchase Tax', relation='purchase_tax_ids',
                                        default=lambda self: self.env['account.tax'].search([('id', '=', 5)]).ids)
    sales_tax_ids = fields.Many2many('account.tax', string='Sales Tax', relation='sales_tax_ids',
                                     default=lambda self: self.env['account.tax'].search([('id', '=', 1)]).ids)
    total_cost = fields.Float("Total Cost With Tax")
    total_income = fields.Float("Total Income With Tax")
    difference = fields.Float("Difference")
    hotel_booking_transportation_id = fields.Many2one('hotel.booking.transportation')
    account_move_id = fields.Many2one('account.move', 'Bill')
    account_move = fields.Many2one('account.move', 'Invoice')

    @api.onchange('departure_date', 'return_date')
    def calc_days(self):
        for line in self:
            if line.departure_date and line.return_date:
                date_format = '%Y-%m-%d'
                from_date = line.departure_date
                to_date = line.return_date
                d1 = datetime.strptime(str(from_date), date_format)
                d2 = datetime.strptime(str(to_date), date_format)
                line.days = (d2 - d1).days
            else:
                line.days = 0.0

    @api.depends('hotel_booking_transportation_id')
    def _compute_available_packages(self):
        for rec in self:
            rec.customer_available_package_ids = [(6, 0, self.env['hotel.transport.package'].search([]).ids)]

    @api.onchange('hotel_booking_transportation_id')
    def _onchange_hotel_booking_transportation_id(self):
        if self.hotel_booking_transportation_id:
            self.customer_package_id = self.hotel_booking_transportation_id.customer_package_id
            self.travel_agent_package_id = self.hotel_booking_transportation_id.travel_agent_package_id

    def create_transportation_bill(self):
        account_move_obj = self.env['account.move']
        for line in self:
            bill_create_obj = account_move_obj.create({
                'move_type': 'in_invoice',
                'transportation_booking_id': line.id,
                'date': line.create_date,
                'invoice_date': line.create_date,
                'invoice_line_ids': [(0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'price_unit': line.cost_price,
                    'tax_ids': line.purchase_tax_ids.ids,
                    'quantity': line.no_of_bus,
                })],
                'partner_id': line.hotel_booking_transportation_id.travel_agent_name.id,
                'ref': line.hotel_booking_transportation_id.name,
            })
            self.account_move_id = bill_create_obj.id

    @api.constrains('cost_price', 'no_of_bus', 'purchase_tax_ids')
    def update_transportation_bill(self):
        for line in self:
            if line.account_move_id and line.hotel_booking_transportation_id.state == 'draft':
                line.account_move_id.invoice_line_ids = [(5, 0, 0)]
                line.account_move_id.update({
                    'move_type': 'in_invoice',
                    'transportation_booking_id': line.id,
                    'date': line.create_date,
                    'invoice_date': line.create_date,
                    'invoice_line_ids': [(0, 0, {
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'price_unit': line.cost_price,
                        'tax_ids': line.purchase_tax_ids.ids,
                        'quantity': line.no_of_bus,
                    })]
                })

    def create_transportation_invoice(self):
        account_move_objs = self.env['account.move']
        for line in self:
            account_move_objs = account_move_objs.create({
                'move_type': 'out_invoice',
                'transportation_booking_id': line.id,
                'date': line.create_date,
                'invoice_date': line.create_date,
                'invoice_line_ids': [(0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'price_unit': line.sell_price,
                    'tax_ids': line.sales_tax_ids.ids,
                    'quantity': line.no_of_bus,
                })],
                'partner_id': line.hotel_booking_transportation_id.partner_id.id,
                'ref': line.hotel_booking_transportation_id.name,
            })
            self.account_move = account_move_objs.id

    @api.constrains('sell_price', 'no_of_bus', 'sales_tax_ids')
    def update_transportation_invoice(self):
        for line in self:
            if line.account_move and line.hotel_booking_transportation_id.state == 'draft':
                line.account_move.invoice_line_ids = [(5, 0, 0)]
                line.account_move.update({
                    'move_type': 'out_invoice',
                    'transportation_booking_id': line.id,
                    'date': line.create_date,
                    'invoice_date': line.create_date,
                    'invoice_line_ids': [(0, 0, {
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'price_unit': line.sell_price,
                        'tax_ids': line.sales_tax_ids.ids,
                        'quantity': line.no_of_bus,
                    })]
                })
                self.update({'account_move': line.account_move})

    @api.onchange('cost_price', 'sell_price', 'no_of_bus')
    def _onchange_price_or_bus_count(self):
        if self.hotel_booking_transportation_id:
            self.hotel_booking_transportation_id._compute_cost_totals()



    # @api.onchange('cost_price', 'sell_price', 'days', 'tax_ids')
    # def calc_totals(self):
    #     total_cost_list = []
    #     total_taxes_list = []
    #     total_sell_price_list = []
    #     total_days = []
    #     self.days = 0
    #     for record in self:
    #         total_cost_list.append(record.cost_price)
    #         total_sell_price_list.append(record.sell_price)
    #         total_days.append(record.days)
    #         for tax in record.tax_ids:
    #             total_taxes_list.append(tax.amount)
    #     self.total_cost = sum(total_cost_list) * sum(total_taxes_list)
    #     self.total_income = sum(total_sell_price_list) * sum(total_days) * sum(total_taxes_list)
    # self.difference = self.total_income - self.total_cost
    # print(self.total_income)
