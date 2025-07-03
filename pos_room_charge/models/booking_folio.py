from odoo import fields, models, api
import logging
logger = logging.getLogger(__name__)


class Folio(models.Model):
    _inherit = 'booking.folio'

    def prepare_invoice_lines(self, lines):
        invoice_line_vals = super().prepare_invoice_lines(lines)
        logger.info('calllled prepare_invoice_lines from foliooooo')
        for line_tuple in invoice_line_vals:
            line_data = line_tuple[2]
            if line_data.get('pos_order_ref'):
                logger.info(f'inherittttt line_data folio {line_data}')
                line = self.env['booking.folio.line'].sudo().browse(line_data.get('folio_line_id'))
                # Example: get taxes from line.tax_ids if available
                logger.info(f'inherittttt line_data folio {line}')
                tax_ids = line.tax_ids.ids if line.tax_ids else []
                # Update tax_ids field
                line_data['tax_ids'] = [(6, 0, tax_ids)]
        logger.info(f'inherittttt invoice_line_vals folio {invoice_line_vals}')
        return invoice_line_vals

