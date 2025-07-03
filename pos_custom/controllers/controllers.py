# -*- coding: utf-8 -*-
# from odoo import http


# class PosCustom(http.Controller):
#     @http.route('/pos_custom/pos_custom', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_custom/pos_custom/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_custom.listing', {
#             'root': '/pos_custom/pos_custom',
#             'objects': http.request.env['pos_custom.pos_custom'].search([]),
#         })

#     @http.route('/pos_custom/pos_custom/objects/<model("pos_custom.pos_custom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_custom.object', {
#             'object': obj
#         })
