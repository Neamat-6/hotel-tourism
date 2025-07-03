from odoo import fields, models, api


class FolioAmendStay(models.Model):
    _inherit = 'folio.amend.stay'
    
    def prepare_folio_line(self, folio, day, amount, line_type):
        result = super(FolioAmendStay, self).prepare_folio_line(folio, day, amount, line_type)
        if line_type == 'service_tax':
            result['particulars'] = 'Service Tax'
            result['type'] = 'tax'
            result['tax_type'] = 'service'
        return result

    def create_folio_lines(self, folio, day, prices):
        res = super(FolioAmendStay, self).create_folio_lines(folio, day, prices)
        price_service_tax = prices['price_service_tax']
        if price_service_tax > 1:
            self.env['booking.folio.line'].create(self.prepare_folio_line(folio, day, price_service_tax, 'service_tax'))
        return res

    def create_service_folio_line(self, folio, service, date, folio_line, old_line):
        res = super(FolioAmendStay, self).create_service_folio_line(folio, service, date, folio_line, old_line)
        service_tax_line = folio.line_ids.filtered(lambda l: l.related_line_id.id == old_line.id and l.tax_type == 'service')
        if service_tax_line:
            self.env['booking.folio.line'].create({
                'folio_id': folio.id,
                'day': date,
                'amount': service_tax_line.amount,
                'particulars': service.service_id.name + ' Service Tax',
                'type': service.service_id.type,
                'is_service_tax': True,
                'related_line_id': folio_line.id,
                'tax_type': 'service',
            })
        return res
