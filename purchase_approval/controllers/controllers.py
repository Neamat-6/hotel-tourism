# -*- coding: utf-8 -*-
# from odoo import http


# class PurchaseApproval(http.Controller):
#     @http.route('/purchase_approval/purchase_approval', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_approval/purchase_approval/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_approval.listing', {
#             'root': '/purchase_approval/purchase_approval',
#             'objects': http.request.env['purchase_approval.purchase_approval'].search([]),
#         })

#     @http.route('/purchase_approval/purchase_approval/objects/<model("purchase_approval.purchase_approval"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_approval.object', {
#             'object': obj
#         })
