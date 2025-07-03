from odoo import fields, models, api


class BookingSource(models.Model):
    _name = 'booking.source'
    _description = 'Booking Source'

    name = fields.Char()
    account_account_id = fields.Many2one('account.account', string='Account', company_dependent=True)
    source = fields.Selection(selection=[
        ('online_agent', 'Online Travel Agent'),
        ('company', 'Company'),
        ('direct', 'Direct'),
        ('government_booking', 'Government Booking'),
        ('contract_booking', 'Contract Booking'),
        ('allotment_booking', 'Allotment Booking'),
    ])


class BusinessSource(models.Model):
    _name = 'business.source'
    _description = 'Business Source'

    name = fields.Char()
