from odoo import fields, models, api


class TransportationLocations(models.Model):
    _name = 'transportation.locations'
    _description = 'Transportation Locations'

    name = fields.Char(translate=True)


class TransportationLocationLine(models.Model):
    _name = 'transportation.location.line'
    _description = 'Transportation Location Line'

    from_location = fields.Many2one('transportation.locations', string="From")
    to_location = fields.Many2one('transportation.locations', string="To")
    contract_id = fields.Many2one('transportation.contract')
