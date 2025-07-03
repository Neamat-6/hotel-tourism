from odoo import fields, models, api
from odoo.osv import expression


class ShomoosCountry(models.Model):
    _name = 'shomoos.country'
    _description = 'Shomoos Country'
    _rec_name = 'arabic_title'
    _order = 'code'

    arabic_title = fields.Char(required=True)
    english_title = fields.Char(required=True)
    code = fields.Char(required=True)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', '|', ('arabic_title', operator, name), ('english_title', operator, name), ('code', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
