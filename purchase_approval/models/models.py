from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('first_approval', 'First Approval'),
        ('second_approval', 'Second Approval'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    def action_first_approval(self):
        self.ensure_one()
        if not self.env.user.has_group('purchase_approval.group_first_approver'):
            raise ValidationError(_("You do not have permission for first approval."))
        self.state = 'first_approval'

    def action_second_approval(self):
        self.ensure_one()
        if not self.env.user.has_group('purchase_approval.group_second_approver'):
            raise ValidationError(_("You do not have permission for second approval."))
        self.state = 'second_approval'

    def button_confirm(self):
        for order in self:
            if order.state not in ['second_approval', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    # def button_confirm(self):
    #     if self.state != 'second_approval':
    #         raise ValueError("Purchase order must be in second approval stage before confirmation.")
    #     return super().button_confirm()
