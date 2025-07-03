from odoo import fields, models, api
from odoo.osv import expression


class ShomoosIdentityType(models.Model):
    _name = 'shomoos.identity.type'
    _description = 'Shomoos Identity'
    _rec_name = 'ar_name'
    _order = 'code'

    ar_name = fields.Char(required=True)
    en_name = fields.Char(required=True)
    code = fields.Char(required=True)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', '|', ('ar_name', operator, name), ('en_name', operator, name),
                      ('code', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
