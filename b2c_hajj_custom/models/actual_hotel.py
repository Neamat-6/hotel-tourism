from odoo import fields, models, api



class ActualHotel(models.Model):
    _name = 'actual.hotel'
    _description = 'Actual Hotel Name'

    name = fields.Char(required=True, string="Hotel Name")
    hotel_id = fields.Many2one('hotel.hotel', required=True, string="Hotel Category")


    @api.model
    def create(self, vals):
        partner_vals = {
            'name': vals['name'],
            'is_company': True,
            'hotel_id': vals['hotel_id']
        }
        self.env['res.partner'].create(partner_vals)
        return super(ActualHotel, self).create(vals)
