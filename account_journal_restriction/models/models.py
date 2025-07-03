# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class YDSResUser(models.Model):
    _inherit = 'res.users'

    user_allowed_journals_ids = fields.Many2many(
        'account.journal',
        'journal_user_id',
        'user_id',
        'journal_id',
        'Allowd User')

    user_hidden_journals_ids = fields.Many2many(
        'account.journal',
        'journal_user_hidden_rel',
        'user_id',
        'journal_id',
        string='Hidden Journals'
    )


class YDSAccountJournal(models.Model):
    _inherit = 'account.journal'

    journal_allowed_users = fields.Many2many(
        'res.users',
        'journal_user_id',
        'journal_id',
        'user_id',
        'Allowd Access Users')

    journal_hidden_users = fields.Many2many(
        'res.users',
        'journal_user_hidden_rel',
        'journal_id',
        'user_id',
        string='Hidden Users'
    )


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def create(self, vals):
        user = self.env.user
        journal_id = vals.get('journal_id')
        if journal_id and journal_id not in user.user_hidden_journals_ids.ids:
            raise UserError("You are not allowed to use this journal for payments. Please select a different journal.")
        return super(AccountPayment, self).create(vals)

    def write(self, vals):
        user = self.env.user
        journal_id = vals.get('journal_id')
        if journal_id and journal_id not in user.user_hidden_journals_ids.ids:
            raise UserError("You are not allowed to use this journal for payments. Please select a different journal.")
        return super(AccountPayment, self).write(vals)


