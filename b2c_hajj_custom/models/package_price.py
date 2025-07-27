from odoo import fields, models, api

class PackageSalePrice(models.Model):
    _name = 'package.sale.price'
    _description = 'Package sale price'

    room_type = fields.Selection([('1', 'Single'), ('2', 'Double'),('3', 'Triple'),('4', 'Quad'), ('5', 'Quintuple')], string='Room Type', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id.id)
    price = fields.Monetary(string='Adult Price', required=True, currency_field='currency_id')
    child_price = fields.Monetary(string='Child Price', required=True, currency_field='currency_id')
    baby_price = fields.Monetary(string='Baby Price', required=True, currency_field='currency_id')
    package_id = fields.Many2one('booking.package', string='Package ID', required=True, ondelete='cascade')

    _sql_constraints = [('room_type_sale_uniq', 'UNIQUE(room_type, package_id)', 'Room Type must be unique per Package!')]



class PackagePrice(models.Model):
    _name = 'package.price'
    _description = 'Package sale and purchase price'
    _rec_name = 'room_type'

    room_type = fields.Selection([('double', 'Double'),('triple', 'Triple'),('quad', 'Quad')], string='Room Type', required=True)
    price_type = fields.Selection([('sale', 'Sale Price'), ('purchase', 'Purchase Price')], string='Price Type', required=True)
    makkah_price = fields.Float(string='Makkah Price')
    madinah_price = fields.Float(string='Madinah Price')
    arf_price = fields.Float(string='Arf Price')
    minnah_price = fields.Float(string='Minnah Price')
    main_hotel_price = fields.Float(string='Main Hotel Price')
    flight_price = fields.Float(string='Flight Price', compute='_compute_flight_price')
    extra_price = fields.Float(string='Extra Price', compute='_compute_extra_price')
    total_price_per_pilgrim = fields.Float(string='Total per Pilgrim', compute='_compute_total_price_per_pilgrim')
    total_price_per_group = fields.Float(string='Total per Group', compute='_compute_total_price_per_group')
    pilgrim_count_sale = fields.Integer(string='Pilgrim Count', compute='_compute_pilgrim_count_sale')
    pilgrim_count_purchase = fields.Integer(string='Pilgrim Count', compute='_compute_pilgrim_count_purchase')
    package_id = fields.Many2one('booking.package', string='Package ID', required=True, ondelete='cascade')

    _sql_constraints = [('room_type_price_type_package_uniq', 'UNIQUE(room_type, price_type, package_id)', 'Room Type and Price Type must be unique per Package!')]


    @api.depends('makkah_price', 'madinah_price', 'arf_price', 'minnah_price', 'main_hotel_price', 'flight_price', 'extra_price')
    def _compute_total_price_per_pilgrim(self):
        for record in self:
            record.total_price_per_pilgrim = sum([
                record.makkah_price,
                record.madinah_price,
                record.arf_price,
                record.minnah_price,
                record.main_hotel_price,
                record.flight_price,
                record.extra_price
            ])

    @api.depends('room_type', 'package_id')
    def _compute_pilgrim_count_sale(self):
        for record in self:
            record.pilgrim_count_sale = 0
            if record.room_type == 'double':
                record.pilgrim_count_sale = record.package_id.makkah_double_total_beds
            elif record.room_type == 'triple':
                record.pilgrim_count_sale = record.package_id.makkah_triple_total_beds
            elif record.room_type == 'quad':
                record.pilgrim_count_sale = record.package_id.makkah_quad_total_beds

    @api.depends('room_type', 'package_id')
    def _compute_pilgrim_count_purchase(self):
        for record in self:
            record.pilgrim_count_purchase = 0
            if record.room_type == 'double':
                record.pilgrim_count_purchase = record.package_id.makkah_double_male_booked_beds + record.package_id.makkah_double_female_booked_beds
            elif record.room_type == 'triple':
                record.pilgrim_count_purchase = record.package_id.makkah_triple_male_booked_beds + record.package_id.makkah_triple_female_booked_beds
            elif record.room_type == 'quad':
                record.pilgrim_count_purchase = record.package_id.makkah_quad_male_booked_beds + record.package_id.makkah_quad_female_booked_beds

    @api.depends('total_price_per_pilgrim', 'pilgrim_count_sale', 'pilgrim_count_purchase', 'price_type')
    def _compute_total_price_per_group(self):
        for record in self:
            record.total_price_per_group = 0
            if record.price_type == 'sale':
                record.total_price_per_group = record.total_price_per_pilgrim * record.pilgrim_count_sale
            elif record.price_type == 'purchase':
                record.total_price_per_group = record.total_price_per_pilgrim * record.pilgrim_count_purchase

    @api.onchange('price_type','package_id','package_id.flight_sale_price', 'package_id.flight_purchase_price')
    def _compute_flight_price(self):
        for record in self:
            record.flight_price = 0.0
            if record.price_type == 'sale':
                record.flight_price = record.package_id.flight_sale_price
            else:
                record.flight_price = record.package_id.flight_purchase_price

    @api.onchange('price_type', 'package_id', 'package_id.extra_service_sale',
                  'package_id.extra_service_purchase')
    def _compute_extra_price(self):
        for record in self:
            record.extra_price = 0.0
            if record.price_type == 'sale':
                record.extra_price = record.package_id.extra_service_sale
            else:
                record.extra_price = record.package_id.extra_service_purchase