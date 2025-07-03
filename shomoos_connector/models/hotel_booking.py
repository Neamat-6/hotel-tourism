from odoo import fields, models


class Booking(models.Model):
    _inherit = 'hotel.booking'

    apply_shomoos = fields.Boolean(compute='get_shomoos_state')
    check_shomoos_transaction = fields.Boolean(compute='check_about_transaction')
    error_msg = fields.Text()

    def get_shomoos_state(self):
        for rec in self:
            if rec.company_id.apply_shomoos:
                rec.apply_shomoos = True
            else:
                rec.apply_shomoos = False

    def shomoos_state(self):
        pass

    def check_about_transaction(self):
        for rec in self:
            folios_without_shomoos = []
            if rec.folio_ids:
                for folio in rec.folio_ids:
                    if not folio.shomoos_transactionID:
                        rec.check_shomoos_transaction = True
                        folios_without_shomoos.append(folio.name)

                if folios_without_shomoos:
                    rec.error_msg = "Folios missing Shomoos transaction ID: " + ', '.join(folios_without_shomoos)
                else:
                    rec.check_shomoos_transaction = False
                    rec.error_msg = "All folios have Shomoos transaction IDs."
            else:
                rec.check_shomoos_transaction = False
                rec.error_msg = "No folios found."
