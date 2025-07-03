from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'


    categ_ids = fields.Many2many('product.category', string='Product Categories')
    device_token = fields.Char('FCM Device Token')


    def write(self, vals):
        res = super().write(vals)
        # Clear caches after writing
        self.clear_caches()
        return res