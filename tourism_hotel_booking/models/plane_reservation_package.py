from odoo import api, fields, models


class PlaneReservationPackage(models.Model):
    _name = 'plane.reservation.package'
    _description = 'Plane Reservation Package'

    reservation_package_id = fields.Many2one("reservation.package")
    plane_contract_id = fields.Many2one("hotel.contract", domain=[('contract_type', '=', 'transportation'),('state','!=',''),
                                                                 ('transportation_type', '=', 'plane')], string='Plane Contract')
    plane_company_id = fields.Many2one('res.partner', related='plane_contract_id.plane_company')
    vendor = fields.Many2one('res.partner', related='plane_contract_id.vendor')
    plane_type_ids = fields.Many2many("plane.type")
    plane_type_id = fields.Many2one("plane.type", "Plane Type")
    unit_price = fields.Float("Unit Price", compute='get_unit_price')

    @api.onchange("plane_contract_id")
    def get_contract_info(self):
        for record in self:
            if record.plane_contract_id:
                record.plane_type_ids = record.plane_contract_id.plane_contract_ids.mapped('plane_type_id').ids

    @api.onchange('plane_type_id')
    def get_unit_price(self):
        for record in self:
            if record.plane_type_id:
                record.unit_price = sum(record.plane_contract_id.plane_contract_ids.filtered(lambda l: l.plane_type_id == record.plane_type_id).mapped('unit_price'))
            else:
                record.unit_price = 0.0
