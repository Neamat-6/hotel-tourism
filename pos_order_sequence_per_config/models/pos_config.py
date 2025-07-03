from odoo import fields, models, api, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pos_sequence_id = fields.Many2one(
        'ir.sequence',
        string='POS Sequence',
        help="This sequence will be used to generate the order number in the POS.",
    )

    def get_next_pos_config_sequence(self):
        """
        This method returns the next sequence number for the current POS configuration.
        It is used to generate the order number in the POS.
        """
        if self.pos_sequence_id:
            return self.pos_sequence_id.next_by_id()
        return False