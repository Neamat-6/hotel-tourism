from odoo import fields, models, api
from odoo.exceptions import ValidationError


class HotelContract(models.Model):
    _name = 'hotel.contract.management'

    name = fields.Char("Name")
    vendor = fields.Many2one('res.partner', string="Supplier", required=True, domain="[('hotel_id', '=', hotel_id)]")
    hotel_id = fields.Many2one('hotel.hotel', copy=False, required=True, string="Hotel Category",)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, readonly=1)
    room_type_id = fields.Many2one('room.type', domain="[('company_id', '=', company_id)]")
    floor_id = fields.Many2one('hotel.floor', domain="[('company_id', '=', company_id)]")
    start = fields.Integer(default=101)
    count = fields.Integer(default=1)
    type = fields.Selection([('hotel', 'Hotel'), ('transportation', 'Transportation')],
                            "Contract Type", copy=False, default='hotel')
    line_ids = fields.One2many(comodel_name="hotel.contract.management.line", inverse_name="contract_id")
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order", readonly=True, copy=False)
    purchase_currency_id = fields.Many2one(
        'res.currency',
        related='purchase_order_id.currency_id',
        string='Purchase Currency',
        store=True,
        readonly=True
    )
    purchase_price = fields.Monetary(string="Purchase Price",
                                     related='purchase_order_id.amount_total',
                                     currency_field='purchase_currency_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('po_created', 'Purchased')
    ], default='draft', string="Status")
    date_from = fields.Date("Start Date", required=True)
    date_to = fields.Date("End Date", required=True)
    is_expired = fields.Boolean("Is Expired", default=False)
    generate_room = fields.Boolean("Generate Rooms", default=False)
    booking_no = fields.Char('Booking Ref')

    _sql_constraints = [('check_dates', 'CHECK(date_from < date_to)', 'End Date must be greater than Start Date!')]

    @api.model
    def _cron_update_contract_expiry(self):
        """This method is called daily via a scheduled action"""
        contracts = self.search([])
        today = fields.Date.today()
        for record in contracts:
            record.is_expired = bool(record.date_to and record.date_to < today)

    def action_confirm(self):
        self.state = 'confirm'

    def action_draft(self):
        self.state = 'draft'

    def button_generate_rooms(self):
        clean = self.env.ref('hotel_booking.hotel_room_status_clean').id
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
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
        self.generate_room = True

    def button_create_purchase_order(self):
        po_vals = {
            'partner_id': self.vendor.id,
            'company_id': self.company_id.id,
            'booking_no': self.booking_no,
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

    _sql_constraints = [
        ('unique_room_type_per_contract', 'unique(contract_id, room_type_id)',
         'Room type must be unique per contract.')
    ]

    contract_id = fields.Many2one('hotel.contract.management')
    hotel_id = fields.Many2one('hotel.hotel', related='contract_id.hotel_id')
    room_type_id = fields.Many2one('room.type', required=True, domain="[('company_id.related_hotel_id', '=', hotel_id)]")
    floor_id = fields.Many2one('hotel.floor', domain="[('company_id.related_hotel_id', '=', hotel_id)]")
    start = fields.Integer(default=101, required=True)
    count = fields.Integer(default=1, required=True)
    unit_price = fields.Monetary("Unit Price", required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, readonly=1)
    currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)
    booked_count = fields.Integer(string="Booked Count", compute="_compute_booked_count", store=False)

    @api.constrains('count', 'booked_count')
    def _check_booked_less_than_count(self):
        for rec in self:
            if rec.booked_count > rec.count:
                raise ValidationError(f"Booked count ({rec.booked_count}) cannot exceed total count ({rec.count}) for {rec.room_type_id.name}.")

    def _compute_booked_count(self):
        Package = self.env['booking.package'].sudo()
        for line in self:
            hotel_type = line.contract_id.hotel_id.type  # 'makkah', 'madinah', or 'hotel'

            if hotel_type == 'makkah':
                domain = [('makkah_contract_id', '=', line.contract_id.id)]
                qty_field = {
                    1: 'makkah_no_single',
                    2: 'makkah_no_double',
                    3: 'makkah_no_triple',
                    4: 'makkah_no_quad',
                    5: 'makkah_no_quint',
                }
            elif hotel_type == 'madinah':
                domain = [('madinah_contract_id', '=', line.contract_id.id)]
                qty_field = {
                    1: 'madinah_no_single',
                    2: 'madinah_no_double',
                    3: 'madinah_no_triple',
                    4: 'madinah_no_quad',
                    5: 'madinah_no_quint'
                }
            elif hotel_type == 'hotel':
                domain = [('main_hotel_contract_id', '=', line.contract_id.id)]
                qty_field = {
                    1: 'hotel_no_single',
                    2: 'hotel_no_double',
                    3: 'hotel_no_triple',
                    4: 'hotel_no_quad',
                    5: 'hotel_no_quint'
                }
            else:
                line.booked_count = 0
                continue  # Unknown type — skip

            # Find matching packages
            packages = Package.search(domain)

            # Determine quantity field based on room type
            mini = line.room_type_id.mini_adults
            field_name = qty_field.get(mini)

            if field_name:
                line.booked_count = sum(getattr(p, field_name, 0) for p in packages)
            else:
                line.booked_count = 0


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    booking_no = fields.Char('Booking Ref')

# class TransportationLine(models.Model):
#     _name = 'transportation.line'
#
#     trans_contract_id = fields.Many2one('hotel.contract.management')
#     no_buses = fields.Char('No. of Buses')
#     transportation_contract_no = fields.Char("Transportation Contract No.")
#     unit_price = fields.Monetary("Unit Price", required=True)
#     currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)
