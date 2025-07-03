from odoo import api, fields, models
from hijri_converter import convert


class ResPartner(models.Model):
    _inherit = 'res.partner'

    shomoos_nationality_id = fields.Many2one('shomoos.nationality', "Nationality")
    shomoos_country_id = fields.Many2one('shomoos.country', "Country")
    shomoos_identity = fields.Many2one("shomoos.identity.type", 'Identity Type')
    shomoos_identity_no = fields.Char('Identity Number', )
    shomoos_date_of_birth = fields.Date("Date Of Birth", )
    date_of_birth_hijri = fields.Date("Date Of Birth (Hijri)")

    @api.onchange('shomoos_date_of_birth')
    def compute_hijri_date(self):
        for record in self:
            if record.shomoos_date_of_birth:
                hijri_date = convert.Gregorian(record.shomoos_date_of_birth.year, record.shomoos_date_of_birth.month,
                                               record.shomoos_date_of_birth.day).to_hijri()
                # hijri_month = hijri_date.month_name()
                record.date_of_birth_hijri = str(hijri_date)
            else:
                record.date_of_birth_hijri = False

    @api.onchange('date_of_birth_hijri')
    def compute_from_hijri(self):
        for record in self:
            if record.date_of_birth_hijri:
                Gregorian_date = convert.Hijri(record.date_of_birth_hijri.year, record.date_of_birth_hijri.month,
                                               record.date_of_birth_hijri.day).to_gregorian()
                record.shomoos_date_of_birth = str(Gregorian_date)
            else:
                record.shomoos_date_of_birth = False
