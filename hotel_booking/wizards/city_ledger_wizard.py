from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class CityLedgerWizard(models.TransientModel):
    _name = 'city.ledger.wizard'
    _description = 'City Ledger'

    line_ids = fields.One2many('city.ledger.line', 'wizard_id')
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    partner_id = fields.Many2one('res.partner', "Partner", domain=[('is_city_ledger', '=', True)])
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def generate_report(self):
        self.ensure_one()
        return self.env['city.ledger.report'].create_report(self.date_from, self.date_to, self.partner_id, self.company_id)

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise ValidationError(_('Check in Date From cannot be earlier than Check In Date To !'))

    def get_city_ledger(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        date_from = self.date_from
        date_to = self.date_to
        partner_id = self.partner_id
        company_id = self.company_id

        account_journal_obj = self.env['account.journal'].search([('is_city_ledger', '=', True)], limit=1)

        if date_from:
            domain.append(('date', '>', date_from))
        if date_to:
            domain.append(('date', '<', date_to))
        if partner_id:
            domain.append(('partner_id', '=', partner_id.id))
        if company_id:
            domain.append(('company_id', '=', company_id.id))

        domain.append(('journal_id', '=', account_journal_obj.id))

        account_move_line = self.env['account.move.line'].search(domain)

        for move in account_move_line:
            name = move['name']
            date = move['date']
            partner_id = move['partner_id']
            room_id = move['room_id']
            credit = move['credit']
            debit = move['debit']
            balance = move['credit'] + move['debit']

            if move:
                self.env['city.ledger.line'].create({
                    'wizard_id': self.id,
                    'name': name,
                    'date': date,
                    'partner_id': partner_id.id,
                    'room_id': room_id.id,
                    'credit': credit,
                    'debit': debit,
                    'balance': balance,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('City Ledger Report'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'city.ledger.wizard',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_city_ledger_report').with_context(
            landscape=True).report_action(self)


class CityLedgerLine(models.TransientModel):
    _name = 'city.ledger.line'

    wizard_id = fields.Many2one('city.ledger.wizard')
    name = fields.Char("Name")
    date = fields.Date("Date")
    partner_id = fields.Many2one('res.partner', string='Partner')
    room_id = fields.Many2one('hotel.room', string='Room No')
    credit = fields.Float("Credit")
    debit = fields.Float("Debit")
    balance = fields.Float("Balance")
