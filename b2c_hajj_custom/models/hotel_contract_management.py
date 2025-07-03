from odoo import fields, models


class HotelContract(models.Model):
    _name = 'hotel.contract.management'

    name = fields.Char("Name")
    vendor = fields.Many2one('res.partner', string="Supplier", required=True, default=lambda self: self.env.company.partner_id)
    hotel_id = fields.Many2one('hotel.hotel', copy=False, required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, readonly=1)
    room_type_id = fields.Many2one('room.type', domain="[('company_id', '=', company_id)]")
    floor_id = fields.Many2one('hotel.floor', domain="[('company_id', '=', company_id)]")
    start = fields.Integer(default=101)
    count = fields.Integer(default=1)
    type = fields.Selection([('hotel', 'Hotel'), ('transportation', 'Transportation')],
                            "Contract Type", required=True,
                            copy=False)
    line_ids = fields.One2many(comodel_name="hotel.contract.management.line", inverse_name="contract_id")
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order", readonly=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('po_created', 'Purchased')
    ], default='draft', string="Status")
    date_from = fields.Date("Start Date", required=True)
    date_to = fields.Date("End Date", required=True)

    _sql_constraints = [('check_dates', 'CHECK(date_from < date_to)', 'End Date must be greater than Start Date!')]

    def action_confirm(self):
        self.state = 'confirm'

    def action_draft(self):
        self.state = 'draft'

    def button_generate_rooms(self):
        clean = self.env.ref('hotel_booking.hotel_room_status_clean').id
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        for i in range(self.count):
            room_number = self.start + i
            self.env['hotel.room'].create({
                'hotel_id': self.hotel_id.id,
                'company_id': self.company_id.id,
                'name': str(room_number),
                'room_type': self.room_type_id.id,
                'floor_id': self.floor_id.id,
                'state': clean,
                'stay_state': vacant,
            })

    def button_create_purchase_order(self):
        clean = self.env.ref('hotel_booking.hotel_room_status_clean').id
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id

        po_vals = {
            'partner_id': self.vendor.id,
            'company_id': self.company_id.id,
            'origin': self.name,
            'order_line': [],
        }

        if self.type == 'hotel':
            product = self.env['product.product'].sudo().search([('name', '=', 'Room Type Product')], limit=1)
            if not product:
                product = self.env['product.product'].sudo().create({
                    'name': 'Room Type Product',
                    'type': 'service',
                    'categ_id': self.env.ref('product.product_category_all').id,
                    'list_price': 0.0,
                    'standard_price': 0.0,
                })
            product_id = product.id

            for line in self.line_ids:
                for i in range(line.count):
                    room_number = line.start + i
                    self.env['hotel.room'].sudo().create({
                        'hotel_id': self.hotel_id.id,
                        'company_id': self.hotel_id.company_id.id,
                        'name': str(room_number),
                        'room_type': line.room_type_id.id,
                        'floor_id': line.floor_id.id,
                        'state': clean,
                        'stay_state': vacant,
                    })

                po_vals['order_line'].append((0, 0, {
                    'product_id': product_id,
                    'name': f"Room Type: {line.room_type_id.name} (Floor: {line.floor_id.name})",
                    'product_qty': line.count,
                    'price_unit': line.unit_price,
                    'date_planned': fields.Date.today(),
                    'company_id': self.company_id.id,
                }))

        elif self.type == 'transportation':
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

            for trans_line in self.transportation_contract_ids:
                po_vals['order_line'].append((0, 0, {
                    'product_id': product_id,
                    'name': f"Transportation: {trans_line.no_buses}",
                    'product_qty': trans_line.no_buses,
                    'price_unit': trans_line.unit_price,
                    'date_planned': fields.Date.today(),
                    'company_id': self.company_id.id,
                }))

        purchase_order = self.env['purchase.order'].create(po_vals)
        self.purchase_order_id = purchase_order.id
        self.state = 'po_created'


class HotelContractLine(models.Model):
    _name = 'hotel.contract.management.line'

    contract_id = fields.Many2one('hotel.contract.management')
    hotel_id = fields.Many2one('hotel.hotel', related='contract_id.hotel_id')
    room_type_id = fields.Many2one('room.type', required=True, domain="[('company_id.related_hotel_id', '=', hotel_id)]")
    floor_id = fields.Many2one('hotel.floor', domain="[('company_id.related_hotel_id', '=', hotel_id)]")
    start = fields.Integer(default=101, required=True)
    count = fields.Integer(default=1, required=True)
    unit_price = fields.Monetary("Unit Price", required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, readonly=1)
    currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)


# class TransportationLine(models.Model):
#     _name = 'transportation.line'
#
#     trans_contract_id = fields.Many2one('hotel.contract.management')
#     no_buses = fields.Char('No. of Buses')
#     transportation_contract_no = fields.Char("Transportation Contract No.")
#     unit_price = fields.Monetary("Unit Price", required=True)
#     currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)
