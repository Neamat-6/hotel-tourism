from odoo import api, fields, models


class BusReservationPackage(models.Model):
    _name = 'bus.reservation.package'
    _description = 'Bus Reservation Package'

    reservation_package_id = fields.Many2one("reservation.package")
    bus_contract_id = fields.Many2one("hotel.contract",
                                      domain=[('contract_type', '=', 'transportation'), ('state', '!=', 'draft'),
                                              ('transportation_type', '=', 'bus')], string='Bus Contract')
    transportation_company_id = fields.Many2one('res.partner', related='bus_contract_id.transportation_company')
    vendor = fields.Many2one('res.partner', related='bus_contract_id.vendor')
    bus_type_ids = fields.Many2many("bus.type")
    bus_type_id = fields.Many2one("bus.type", "Bus Type")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    unit_price = fields.Float("Unit Price", compute='get_unit_price')

    @api.onchange("bus_contract_id")
    def get_contract_info(self):
        for record in self:
            if record.bus_contract_id:
                record.bus_type_ids = record.bus_contract_id.transportation_contract_ids.mapped('bus_type_id').ids

    @api.onchange('bus_type_id')
    def get_unit_price(self):
        for record in self:
            if record.bus_type_id:
                record.unit_price = sum(record.bus_contract_id.transportation_contract_ids.filtered(lambda l: l.bus_type_id == record.bus_type_id).mapped('unit_price'))
                record.start_date = record.bus_contract_id.transportation_contract_ids.filtered(lambda l: l.bus_type_id == record.bus_type_id).start_date
                record.end_date = record.bus_contract_id.transportation_contract_ids.filtered(lambda l: l.bus_type_id == record.bus_type_id).end_date
            else:
                record.unit_price = 0.0
