# -*- coding: utf-8 -*-
# from odoo import http


# class HotelBookingCrm(http.Controller):
#     @http.route('/hotel_booking_crm/hotel_booking_crm', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hotel_booking_crm/hotel_booking_crm/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hotel_booking_crm.listing', {
#             'root': '/hotel_booking_crm/hotel_booking_crm',
#             'objects': http.request.env['hotel_booking_crm.hotel_booking_crm'].search([]),
#         })

#     @http.route('/hotel_booking_crm/hotel_booking_crm/objects/<model("hotel_booking_crm.hotel_booking_crm"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hotel_booking_crm.object', {
#             'object': obj
#         })
