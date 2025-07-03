from odoo import api, fields, models, _


class CashierCustody(models.Model):
    _name = 'cashier.custody'
    _rec_name = 'user_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_user_id_domain(self):
        res = [('share', '=', False), ('id', '=', self.env.uid)]
        if self.user_has_groups('cashier_custody.group_cashier_manager'):
            res = [('share', '=', False)]
        return res

    status = fields.Selection(selection=[('waiting', 'Waiting For Approved'), ('draft', 'Draft'), ('post', 'Posted'),('closed', 'Closed')], string="Status", default="draft")
    date_from = fields.Date(string="Date From", required=False)
    date_to = fields.Date(string="Date To", required=False, )
    company_ids = fields.Many2many('res.company', string='Hotels', required=True)
    user_id = fields.Many2one(comodel_name="res.users", string="Cashier", required=True, default=lambda self: self.env.uid, domain=lambda self: self._get_user_id_domain())
    account_journal_id = fields.Many2one(comodel_name="account.journal", string="Cashier Journal", required=False,
                                         store=True)
    account_journal_ids = fields.Many2many('account.journal')
    account_payment_ids = fields.One2many(comodel_name="account.payment", inverse_name="cashier_custody_id",
                                          string="closing cashier", required=False, )
    total_amount = fields.Float(digits=(16, 2), readonly=True)
    no_lines = fields.Integer("No.Lines", compute='calc_total_amount', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)
    source_journal_id = fields.Many2one('account.journal', "Source Journal", domain=[('user_id', '=', user_id)])
    des_journal_id = fields.Many2one('account.journal', "Destination Journal",
                                     domain=[('is_casher_journal', '!=', True),
                                             ('type', 'in', ['bank', 'cash']), ('is_city_ledger', '=', False)])
    account_move_ids = fields.One2many("account.move", inverse_name='cashier_custody_id')
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('posted', 'Posted'), ], required=False, default="posted")
    count_journals = fields.Integer(compute='count_journal_entry')
    payment_state = fields.Selection(string="Payment State",
                                     selection=[('closed', 'Closed'), ('not_closed', 'Not Closed'), ], required=True,default="not_closed")
    note = fields.Text("Note")


    @api.onchange('user_id')
    def onchange_user_id(self):
        if self.user_id:
            account_journal_ids = self.env['account.journal'].search([('user_id', '=', self.user_id.id),('type', 'in', ['cash'])])
            if account_journal_ids:
                self.account_journal_ids = account_journal_ids.ids
            else:
                self.account_journal_ids = False
        else:
            self.account_journal_ids = False

    @api.onchange('account_payment_ids')
    def calc_total_amount(self):
        for rec in self:
            if rec.account_payment_ids:
                rec.total_amount = sum(rec.account_payment_ids.filtered(lambda l:l.is_selected_payment).mapped('amount'))
                rec.no_lines = len(rec.account_payment_ids)
            else:
                rec.total_amount = 0.0
                rec.no_lines = 0

    def button_search(self):
        self.account_payment_ids = [(5, 0, 0)]
        domain = []
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))
        if self.payment_state == 'closed':
            domain.append(('closed_cashier', '=', True))
        if self.payment_state == 'not_closed':
            domain.append(('closed_cashier', '=', False))
        if self.state:
            domain.append(('state', '=', self.state))
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        if self.account_journal_id:
            domain.append(('journal_id', '=', self.account_journal_id.id))

        account_payment_objs = self.env['account.payment'].sudo().search(domain)

        account_payment_values = []
        for payment in account_payment_objs:
            vals = {
                'date': payment.date,
                'name': payment.name,
                'journal_id': payment.journal_id.id,
                'booking_id': payment.booking_id.id,
                'folio_id': payment.folio_id.id,
                'payment_method_line_id': payment.payment_method_line_id.id,
                'partner_id': payment.partner_id.id,
                'amount': payment.amount,
                'state': payment.state,
                'closed_cashier': payment.closed_cashier
            }
            account_payment_values.append((4, payment.id, 0))

        self.account_payment_ids = account_payment_values
        self.status = 'closed'

    def button_close_cashier(self):
        for line in self.account_payment_ids.filtered(lambda p: p.is_selected_payment):
            if not line.closed_cashier:
                line.closed_cashier = True
        self.status = 'closed'

    def action_open_journal_entry(self):
        self.ensure_one()
        recs = self.account_move_ids
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'name': _('Journal Entry'),
            'view_mode': 'tree,form',
            'domain': [('id', 'in', recs.ids)]
        }

    def count_journal_entry(self):
        if self.account_move_ids:
            self.count_journals = len(self.account_move_ids)
        else:
            self.count_journals = 0

    def button_toggle_all(self):
        flag = any(self.account_payment_ids.filtered(lambda p: not p.is_selected_payment))
        if flag:
            for line in self.account_payment_ids:
                line.is_selected_payment = True
        else:
            for line in self.account_payment_ids:
                line.is_selected_payment = False

    def print_pdf(self):
        return self.env.ref('hotel_booking_folio.action_guest_ledger_report').with_context(landscape=True).report_action(self)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     result = super().create(vals_list)
    #     result.button_search()
    #     result.status = 'closed'
    #     return result