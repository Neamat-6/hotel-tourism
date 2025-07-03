from odoo import models, api, _
from odoo.exceptions import ValidationError


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    @api.constrains('email', 'mobile', 'name')
    def _unique_email_mobile(self):
        for record in self:
            if record.is_company:
                if not record.email or not record.phone:
                    raise ValidationError(_("Email and Phone is Required"))
                unique_email = self.search([('email', '=ilike', record.email), ('id', '!=', record.id)])
                unique_mobile = self.search([('phone', '=ilike', record.phone), ('id', '!=', record.id)])
                if unique_email and unique_mobile:
                    raise ValidationError(_("Email and Phone must be Unique"))
                elif unique_email:
                    raise ValidationError(_("Email must be Unique"))
                elif unique_mobile:
                    raise ValidationError(_("Mobile Phone must be Unique"))
