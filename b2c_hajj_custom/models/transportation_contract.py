from odoo import fields, models, api
from odoo.exceptions import ValidationError


class TransportationContract(models.Model):
    _name = 'transportation.contract'
    _rec_name = 'transportation_contract_no'

    transportation_company = fields.Many2one('res.partner', domain=[('is_transportation_company', '=', True)])
    no_buses = fields.Char('No. of Buses')
    transportation_contract_no = fields.Char("Transportation Contract No.")
    location_lines = fields.One2many('transportation.location.line', 'contract_id')
    pilgrims_no = fields.Integer(string='Pilgrims NO.')
    booked_no = fields.Integer(string='Booked NO.', compute='_compute_booked_no')
    available_no = fields.Integer(string='Available NO.', compute='_compute_available_no')
    cost_price = fields.Float(string='Cost Price')


    # def button_create_purchase_order(self):
    #     clean = self.env.ref('hotel_booking.hotel_room_status_clean').id
    #     vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
    #
    #     po_vals = {
    #         'partner_id': self.vendor.id,
    #         'company_id': self.company_id.id,
    #         'origin': self.name,
    #         'order_line': [],
    #     }
    #
    #     if self.type == 'hotel':
    #         product = self.env['product.product'].sudo().search([('name', '=', 'Room Type Product')], limit=1)
    #         if not product:
    #             product = self.env['product.product'].sudo().create({
    #                 'name': 'Room Type Product',
    #                 'type': 'service',
    #                 'categ_id': self.env.ref('product.product_category_all').id,
    #                 'list_price': 0.0,
    #                 'standard_price': 0.0,
    #             })
    #         product_id = product.id
    #
    #         for line in self.line_ids:
    #             for i in range(line.count):
    #                 room_number = line.start + i
    #                 self.env['hotel.room'].sudo().create({
    #                     'hotel_id': self.hotel_id.id,
    #                     'company_id': self.hotel_id.company_id.id,
    #                     'name': str(room_number),
    #                     'room_type': line.room_type_id.id,
    #                     'floor_id': line.floor_id.id,
    #                     'state': clean,
    #                     'stay_state': vacant,
    #                 })
    #
    #             po_vals['order_line'].append((0, 0, {
    #                 'product_id': product_id,
    #                 'name': f"Room Type: {line.room_type_id.name} (Floor: {line.floor_id.name})",
    #                 'product_qty': line.count,
    #                 'price_unit': line.unit_price,
    #                 'date_planned': fields.Date.today(),
    #                 'company_id': self.company_id.id,
    #             }))
    #
    #     elif self.type == 'transportation':
    #         product = self.env['product.product'].sudo().search([('name', '=', 'Transportation Product')], limit=1)
    #         if not product:
    #             product = self.env['product.product'].sudo().create({
    #                 'name': 'Transportation Product',
    #                 'type': 'service',
    #                 'categ_id': self.env.ref('product.product_category_all').id,
    #                 'list_price': 0.0,
    #                 'standard_price': 0.0,
    #             })
    #         product_id = product.id
    #
    #         for trans_line in self.transportation_contract_ids:
    #             po_vals['order_line'].append((0, 0, {
    #                 'product_id': product_id,
    #                 'name': f"Transportation: {trans_line.no_buses}",
    #                 'product_qty': trans_line.no_buses,
    #                 'price_unit': trans_line.unit_price,
    #                 'date_planned': fields.Date.today(),
    #                 'company_id': self.company_id.id,
    #             }))
    #
    #     purchase_order = self.env['purchase.order'].create(po_vals)
    #     self.purchase_order_id = purchase_order.id
    #     self.state = 'po_created'

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
