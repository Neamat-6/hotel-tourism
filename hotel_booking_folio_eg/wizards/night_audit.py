from odoo import fields, models, api


class NightAudit(models.TransientModel):
    _inherit = 'night.audit'

    def prepare_invoice_lines(self, folio, line):
        invoice_line_vals = []
        municipality_price = 0
        default_account = folio.room_id.product_id.categ_id.property_account_income_categ_id.id
        if folio.booking_line_id.price_include_tax:
            price_unit = line.amount
            if line.type == 'room_charge':
                vat_line = folio.line_ids.filtered(
                    lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax
                )
                service_tax_line = folio.line_ids.filtered(
                    lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'service' and not l.is_service_tax
                )
                municipality_line = folio.line_ids.filtered(
                    lambda
                        l: l.day == line.day and l.type == 'tax' and l.tax_type == 'municipality' and not l.is_service_tax
                )
            else:
                vat_line = folio.line_ids.filtered(
                    lambda l: l.tax_type == 'vat' and l.is_service_tax and l.related_line_id.id == line.id
                )
                service_tax_line = folio.line_ids.filtered(
                    lambda l: l.tax_type == 'service' and l.is_service_tax and l.related_line_id.id == line.id
                )
                municipality_line = folio.line_ids.filtered(
                    lambda
                        l: l.tax_type == 'municipality' and l.is_service_tax and l.related_line_id.id == line.id
                )
            if vat_line:
                price_unit += vat_line[0].amount
            if service_tax_line:
                price_unit += service_tax_line[0].amount
            if municipality_line:
                municipality_price = municipality_line[0].amount
        else:
            price_unit = line.amount
        # vals = {
        #     'product_id': folio.room_id.product_id.id,
        #     'name': line.particulars,
        #     'quantity': 1,
        #     'price_unit': price_unit,
        #     'source_booking_id': folio.booking_line_id.id,
        #     'tax_ids': [(6, 0, folio.booking_line_id.tax_id.ids or [])],
        #     'account_id': line.get_account(line.type) or default_account
        # }
        invoice_line_vals.append((0, 0, {
            'product_id': folio.room_id.product_id.id,
            'name': line.particulars,
            'quantity': 1,
            'price_unit': price_unit,
            'source_booking_id': folio.booking_line_id.id,
            'tax_ids': [(6, 0, folio.booking_line_id.tax_id.filtered(lambda l: '15%' in (l.name or '').lower()).ids or [])],
            'account_id': line.get_account(line.type) or default_account,
            'folio_line_id': line.id
        }))
        if municipality_price:
            invoice_line_vals.append((0, 0, {
                'name': f"Municipality Tax",
                'quantity': 1,
                'price_unit': municipality_price,
                'source_booking_id': folio.booking_line_id.id,
                'tax_ids': [(6, 0, folio.booking_line_id.tax_id.filtered(lambda l: '15%' in (l.name or '').lower()).ids or [])],
                'account_id': line.get_account('tax') or default_account,
                'folio_line_id': line.id
            }))
        return invoice_line_vals
