from odoo import fields, models, api
import logging
logger = logging.getLogger(__name__)


class Folio(models.Model):
    _inherit = 'booking.folio'



    def prepare_invoice_lines(self, lines):
        invoice_line_vals = super().prepare_invoice_lines(lines)
        logger.info('calllllllllllllllllled from service charge')
        for line_tuple in invoice_line_vals:
            line_data = line_tuple[2]
            if not line_data.get('pos_order_ref'):
                logger.info(f'inherittttt line_data service charge folio {line_data}')
                # Update tax_ids field
                line_data['tax_ids'] = [(6, 0, self.booking_line_id.tax_id.ids or [])]
            if line_data.get('name') == 'Municipality Tax':
                line_data['name'] = "Service Charge"
        logger.info(f'inherittttt invoice_line_vals service charge folio {invoice_line_vals}')
        return invoice_line_vals


class FolioLine(models.Model):
    _inherit = 'booking.folio.line'

    tax_type = fields.Selection(selection=[
        ('vat', 'VAT'), ('municipality', 'Service Charge'),
    ])

