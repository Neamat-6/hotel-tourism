from odoo import fields, models, api
import logging
logger = logging.getLogger(__name__)

class NightAudit(models.TransientModel):
    _inherit = 'night.audit'


    def prepare_invoice_lines(self, folio, line):
        invoice_line_vals = super().prepare_invoice_lines(folio, line)
        logger.info(f'calllllllllllllllllled night audit from service charge')
        for line_tuple in invoice_line_vals:
            line_data = line_tuple[2]
            if not line_data.get('pos_order_ref'):
                logger.info(f'inherittttt line_data nightttt service charge {line_data}')
                logger.info(f'inherittttt line_data from pos nightttt  service charge{line.particulars}')
                # Update tax_ids field
                line_data['tax_ids'] = [(6, 0, folio.booking_line_id.tax_id.ids or [])]
            if line_data.get('name') == 'Municipality Tax':
                line_data['name'] = "Service Charge"
        logger.info(f'inherittttt invoice_line_vals nighttt service charge {invoice_line_vals}')
        return invoice_line_vals

