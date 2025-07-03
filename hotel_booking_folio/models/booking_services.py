from odoo import fields, models, api


class BookingServices(models.Model):
    _inherit = 'booking.services'

    folio_id = fields.Many2one('booking.folio', ondelete='cascade')
    price = fields.Float()
    price_include_tax = fields.Boolean()
    tax_ids = fields.Many2many('account.tax')
    booking_folio_line_id = fields.Many2one('booking.folio.line', ondelete='cascade')

    def update_folio_service(self):
        folio = self.folio_id
        if self.tax_ids:
            taxes = self.tax_ids.ids
        else:
            taxes = folio.rate_plan_id.tax_ids.ids
        return {
            'type': 'ir.actions.act_window',
            'name': "Update Service",
            'res_model': 'folio.service',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_folio_id': self.folio_id.id if self.folio_id else False,
                'default_service_id': self.service_id.id if self.service_id else False,
                'default_price_type': self.price_type if self.price_type else False,
                'default_type': self.type if self.type else False,
                'default_price': self.price,
                'default_price_include_tax': self.price_include_tax,
                'default_plan_tax_ids': taxes,
                'default_tax_ids': taxes,
                'default_update_existing_service': True,
            }
        }

    def delete_folio_service(self):
        folio_lines = self.folio_id.line_ids
        lines = folio_lines.filtered(
            lambda l: l.type == self.service_id.type and l.particulars == self.service_id.name
        )
        sub_lines = folio_lines.filtered(lambda l: l.related_line_id.id in lines.ids)
        sub_lines.unlink()
        lines.unlink()
        self.unlink()
