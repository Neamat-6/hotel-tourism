from odoo import fields, models, api


class FolioAmendStay(models.Model):
    _inherit = 'folio.amend.stay'

    def button_amend_stay(self):
        res = super(FolioAmendStay, self).button_amend_stay()
        if self.env.company.related_hotel_id.enable_ezee:
            if self.folio_ids:
                folio = self.folio_ids[0]
                company = folio.company_id
                room_type_ids = self.folio_ids.mapped('room_type_id').mapped('id')
                check_in = folio.booking_id.check_in_date
            else:
                folio = self.folio_id
                company = folio.company_id
                room_type_ids = folio.room_type_id.ids
                check_in = folio.check_in_date

            wizard = self.env['ezee.connector'].create({
                'date_from': check_in,
                'date_to': self.new_check_out,
                'action_type': 'update_inventory',
                'company_id': company.id,
                'room_type_ids': [(6, 0, room_type_ids)],
            })
            wizard.button_search()
            wizard.button_update_inventory()
            self.env['audit.trails'].create({
                'booking_id': folio.booking_id.id,
                'folio_id': folio.id,
                'user_id': self.env.user.id,
                'operation': 'ezee',
                'datetime': fields.Datetime.now(),
                'notes': wizard.note
            })

        return res
