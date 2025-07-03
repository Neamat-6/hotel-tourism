# -*- coding: utf-8 -*-
# from odoo import http


# class HotelMenus(http.Controller):
#     @http.route('/hotel_menus/hotel_menus', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hotel_menus/hotel_menus/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hotel_menus.listing', {
#             'root': '/hotel_menus/hotel_menus',
#             'objects': http.request.env['hotel_menus.hotel_menus'].search([]),
#         })

#     @http.route('/hotel_menus/hotel_menus/objects/<model("hotel_menus.hotel_menus"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hotel_menus.object', {
#             'object': obj
#         })
