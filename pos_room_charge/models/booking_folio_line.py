from odoo import models, fields, api, _
import logging
logger = logging.getLogger(__name__)


class BookingFolioLine(models.Model):
    _inherit = 'booking.folio.line'

    tax_ids = fields.Many2many('account.tax', string='Taxes')

    @api.model
    def create_from_pos_order(self, order, room_name):
        logger.info(f'calllled create_from_pos_order from foliooooo {order}')
        logger.info(f"calllled create_from_pos_order liness from foliooooo {order.get('lines')}")
        all_tax_ids = set()
        amount = 0
        description = ''
        service_amount = 0
        service_line = {}
        service_tax_ids = set()
        for line in order.get('lines'):
            line_data = line[2]
            if not line_data.get('is_service_charge'):
                amount += line_data.get('price_subtotal')
                product_name = line_data.get('full_product_name') or ''
                if description:
                    description += ' - '
                description += product_name
                for tax in line_data.get('tax_ids', []):
                    if isinstance(tax, list) and len(tax) == 3 and tax[0] == 6:
                        all_tax_ids.update(tax[2])
                    elif isinstance(tax, int):
                        all_tax_ids.add(tax)
            elif line_data.get('is_service_charge'):
                service_amount += line_data.get('price_subtotal')
                for tax in line_data.get('tax_ids', []):
                    if isinstance(tax, list) and len(tax) == 3 and tax[0] == 6:
                        service_tax_ids.update(tax[2])
                    elif isinstance(tax, int):
                        service_tax_ids.add(tax)
        room_id = self.env['hotel.room'].search([('name', '=', room_name)], limit=1)
        charge_line = {
            'day': fields.Date.today(),
            'particulars': _('Posted from pos'),
            'type': 'food',
            'description': description,
            'create_uid': order.get('user_id'),
            'amount': amount,
            'tax_ids': [(6, 0, list(all_tax_ids))] if all_tax_ids else False,
            'pos_order_ref': order.get('name'),
            'folio_id': room_id.folio_id.id,
            'booking_id': room_id.booking_id.id,
        }
        charge_line = self.env['booking.folio.line'].create(charge_line)
        vat_line = {
            'day': fields.Date.today(),
            'particulars': _('Posted from pos VAT'),
            'type': 'tax',
            'is_service_tax': True,
            'tax_type': 'vat',
            'description': description,
            'create_uid': order.get('user_id'),
            'amount': order.get('amount_tax'),
            'pos_order_ref': order.get('name'),
            'folio_id': room_id.folio_id.id,
            'booking_id': room_id.booking_id.id,
        }
        self.env['booking.folio.line'].create(vat_line)
        if service_amount:
            service_line = {
                'day': fields.Date.today(),
                'particulars': _('Posted from pos Service Charge'),
                'type': 'tax',
                'is_service_tax': True,
                'tax_type': 'municipality',
                'description': f'{description}-Service Charge',
                'create_uid': order.get('user_id'),
                'amount': service_amount,
                'pos_order_ref': order.get('name'),
                'tax_ids': [(6, 0, list(service_tax_ids))] if service_tax_ids else False,
                'related_line_id': charge_line.id,
                'folio_id': room_id.folio_id.id,
                'booking_id': room_id.booking_id.id,
            }
            self.env['booking.folio.line'].create(service_line)
