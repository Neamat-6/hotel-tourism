from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    assistant_embed = fields.Text(string="Assistant Embed Code")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            assistant_embed=self.env['ir.config_parameter'].sudo().get_param('assistant_embed.code', default='')
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('assistant_embed.code', self.assistant_embed)