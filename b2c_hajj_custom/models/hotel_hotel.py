from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HotelHotel(models.Model):
    _inherit = 'hotel.hotel'

    is_camp = fields.Boolean('Is Camp')
    type = fields.Selection(string="Type", selection=[
        ('makkah', 'Makkah'), ('madinah', 'Madinah'), ('arfa', 'Arfa'),
        ('minnah', 'Minnah'), ('hotel', 'Main Shift')
    ])
    contract_no = fields.Char("Contract No.")

    @api.constrains('contract_no')
    def _unique_name(self):
        for record in self:
            contract_no = self.search([('contract_no', '=ilike', record.contract_no), ('id', '!=', record.id)])
            if contract_no:
                raise ValidationError(_("Contract Number Must Be Unique"))

    def action_generate_rooms(self):
        return {
            'name': 'Generate Rooms',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hotel.room.generate',
            'context': {
                'default_hotel_id': self.id,
                'default_company_id': self.company_id.id,
            },
            'target': 'new',
        }

    def action_update_rooms(self):
        return {
            'name': 'Update Rooms',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hotel.room.update',
            'context': {
                'default_hotel_id': self.id,
                'default_company_id': self.company_id.id,
            },
            'target': 'new',
        }
