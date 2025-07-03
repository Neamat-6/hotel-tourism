# -*- coding: utf-8 -*-
# from odoo import http


# class YdsAccountJournalRestriction(http.Controller):
#     @http.route('/yds_account_journal_restriction/yds_account_journal_restriction/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/yds_account_journal_restriction/yds_account_journal_restriction/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('yds_account_journal_restriction.listing', {
#             'root': '/yds_account_journal_restriction/yds_account_journal_restriction',
#             'objects': http.request.env['yds_account_journal_restriction.yds_account_journal_restriction'].search([]),
#         })

#     @http.route('/yds_account_journal_restriction/yds_account_journal_restriction/objects/<model("yds_account_journal_restriction.yds_account_journal_restriction"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('yds_account_journal_restriction.object', {
#             'object': obj
#         })
