from odoo import fields, models, api, _


class FolioReport(models.TransientModel):
    _name = 'folio.report'
    _description = 'Folio Report'

    check_in_from = fields.Date()
    check_in_to = fields.Date()
    check_out_from = fields.Date()
    check_out_to = fields.Date()
    booking_source = fields.Selection(selection=[
        ('online_agent', 'Online Travel Agent'), ('company', 'Company'), ('direct', 'Direct'),
    ])
    online_travel_agent_source = fields.Many2one('res.partner', domain="[('online_travel_agent', '=', True)]")
    company_booking_source = fields.Many2one('res.partner', domain="[('travel_type', '=', 'company')]")
    state_ids = fields.Many2many('folio.report.state', string='States')
    company_id = fields.Many2one('res.company')
    line_ids = fields.One2many('folio.report.line', 'wizard_id')
    partner_id = fields.Many2one('res.partner', string='Guest Name')
    mobile = fields.Char(string='Guest Mobile')
    booking_id = fields.Many2one('hotel.booking', string='Booking Number')
    folio_id = fields.Many2one('booking.folio', string='Ref')
    room_id = fields.Many2one('hotel.room', string='Room Number')

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        if self.check_in_from:
            domain.append(('check_in_date', '>=', self.check_in_from))
        if self.check_in_to:
            domain.append(('check_in_date', '<=', self.check_in_to))
        if self.check_out_from:
            domain.append(('check_out_date', '>=', self.check_out_from))
        if self.check_out_to:
            domain.append(('check_out_date', '<=', self.check_out_to))
        if self.booking_source:
            domain.append(('booking_id.booking_source', '=', self.booking_source))
            if self.booking_source == 'online_agent' and self.online_travel_agent_source:
                domain.append(('booking_id.online_travel_agent_source', '=', self.online_travel_agent_source.id))
            elif self.booking_source == 'company' and self.company_booking_source:
                domain.append(('booking_id.company_booking_source', '=', self.company_booking_source.id))
        if self.state_ids:
            domain.append(('state', 'in', self.state_ids.mapped('type')))
        if self.partner_id:
            domain.append('|')
            domain.append(('partner_id', '=', self.partner_id.id))
            domain.append(('booking_id.partner_id', '=', self.partner_id.id))

        if self.booking_id:
            domain.append(('booking_id', '=', self.booking_id.id))
        if self.room_id:
            domain.append(('room_id', '=', self.room_id.id))
        if self.mobile:
            domain.append('|')
            domain.append(('booking_id.partner_id.mobile', 'ilike', self.mobile))
            domain.append(('partner_id.mobile', 'ilike', self.mobile))

        domain.append(('company_id', '=', self.env.company.id))

        folios = self.env['booking.folio'].sudo().search(domain)
        for folio in folios:
            self.line_ids = [(0, 0, {
                'folio_id': folio.id
            })]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Folio Report'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'folio.report',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking_folio.action_folio_report').report_action(self)

    def print_xlsx(self):
        return self.env.ref('hotel_booking_folio.action_folio_xlsx_report').report_action(self)


class FolioReportLine(models.TransientModel):
    _name = 'folio.report.line'
    _description = 'Folio Report Line'

    wizard_id = fields.Many2one('folio.report')
    folio_id = fields.Many2one('booking.folio')
    booking_id = fields.Many2one('hotel.booking', related='folio_id.booking_id')
    name = fields.Char(related='folio_id.name')
    room_type_id = fields.Many2one('room.type', related='folio_id.room_type_id')
    room_id = fields.Many2one('hotel.room', related='folio_id.room_id')
    check_in = fields.Datetime(related='folio_id.check_in')
    check_out = fields.Datetime(related='folio_id.check_out')
    # amount fields
    price_subtotal = fields.Monetary(related='folio_id.price_subtotal', store=True, string='Subtotal')
    price_total = fields.Monetary(related='folio_id.price_total', store=True, string='Total')
    price_tax = fields.Monetary(related='folio_id.price_tax', store=True, string='Total Tax')
    price_paid = fields.Monetary(related='folio_id.price_paid', store=True, string='Total Paid')
    price_due = fields.Monetary(related='folio_id.price_due', store=True, string='Total Due')
    currency_id = fields.Many2one('res.currency', related='folio_id.currency_id')
    state = fields.Selection(related='folio_id.state')

    def button_open_lines(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Folio",
            'res_model': 'booking.folio',
            'res_id': self.folio_id.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def print_report(self):
        return self.env.ref('hotel_booking.folio_report_action').report_action(self.folio_id)



class FolioReportState(models.Model):
    _name = 'folio.report.state'
    _description = 'Folio Report State'

    name = fields.Char()
    type = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed Waiting Payment'),
        ('checked_in', 'Checked In'), ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled')
    ])
