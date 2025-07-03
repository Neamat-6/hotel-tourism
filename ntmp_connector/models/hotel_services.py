from odoo import fields, models, api


class HotelServices(models.Model):
    _inherit = 'hotel.services'

    ntmp_service_id = fields.Many2one('ntmp.expense.type', string='NTMP Expense')
