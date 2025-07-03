from odoo import fields, models, api



class RoomChargeManagerReport(models.TransientModel):
    _inherit = 'room.charge.manager.report'

    charge_type = fields.Selection([
        ('room_charge', 'Room Charge'),
        ('manual', 'Manual'),
        ('cancellation', 'Cancellation'),
        ('no_show', 'No Show'),
        ('early', 'Early'),
        ('late', 'Late'),
        ('municipality', 'Service Charge'),
        ('vat', 'VAT'),
    ], required=True)


class ExtraChargeManagerReport(models.TransientModel):
    _inherit = 'extra.charge.manager.report'

    tax_type = fields.Selection([
        ('municipality', 'Service Charge'),
        ('vat', 'VAT'),
    ])
