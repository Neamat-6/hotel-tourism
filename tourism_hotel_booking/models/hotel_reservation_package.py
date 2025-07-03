from odoo import api, fields, models


class HotelReservationPackage(models.Model):
    _name = 'hotel.reservation.package'
    _description = 'Hotel Reservation Package'

    reservation_package_id = fields.Many2one("reservation.package")
    hotel_id = fields.Many2one("hotel.hotel", string='Hotel', related='hotel_contract_id.hotel')
    hotel_contract_id = fields.Many2one("hotel.contract", domain=[('contract_type', '=', 'hotel'), ('state', '!=', 'draft')])
    hotel_ids = fields.Many2many("hotel.hotel", string='Hotel')
    room_type_ids = fields.Many2many("hotel.room")
    room_type = fields.Many2one("hotel.room")
    start_date = fields.Date("Start Date", related='hotel_contract_id.start_date', readonly=False)
    end_date = fields.Date("End Date", related='hotel_contract_id.end_date', readonly=False)
    unit_price = fields.Float("Unit Price")

    @api.onchange("hotel_contract_id")
    def get_hotels_info(self):
        for record in self:
            if record.hotel_contract_id:
                record.room_type_ids = record.hotel_contract_id.contract_line.mapped('room_type').ids

    @api.onchange('room_type')
    def get_unit_price(self):
        for record in self:
            if record.room_type:
                record.unit_price = float(record.hotel_contract_id.contract_line.filtered(lambda l: l.room_type == record.room_type).price)
            else:
                record.unit_price = 0.0
