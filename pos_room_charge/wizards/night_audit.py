from odoo import fields, models, api
import logging
logger = logging.getLogger(__name__)


class NightAudit(models.TransientModel):
    _inherit = 'night.audit'

    def prepare_invoice_lines(self, folio, line):
        invoice_line_vals = super().prepare_invoice_lines(folio, line)
        logger.info(f'calllled prepare_invoice_lines from nightttttttt')
        for line_tuple in invoice_line_vals:
            line_data = line_tuple[2]
            if line_data.get('pos_order_ref'):
                logger.info(f'inherittttt line_data nightttt {line_data}')
                logger.info(f'inherittttt line_data from pos nightttt {line.particulars}')
                # Example: get taxes from line.tax_ids if available
                tax_ids = line.tax_ids.ids if line.tax_ids else []
                # Update tax_ids field
                line_data['tax_ids'] = [(6, 0, tax_ids)]
        logger.info(f'inherittttt invoice_line_vals nighttt {invoice_line_vals}')
        return invoice_line_vals