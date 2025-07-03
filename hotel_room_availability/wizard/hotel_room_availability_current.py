# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HotelRoomAvailabilitySheetOpen(models.TransientModel):
    _name = 'hotel.room.availability.sheet.open'
    _description = 'hotel.room.availability.sheet.open'
    hotel_id = fields.Many2one('hotel.hotel', 'Hotel', required=True)


    def open_room_availability_sheet(self):
        view_type = 'form,tree'
        main_hotel =self.hotel_id.id
        sheets = self.env['room.availability'].search([
            ('company_id', '=', main_hotel),
            ('state', '=', 'draft'),('room_availability_ids', '!=', False)])
        rooms = self.env['hotel.room'].search([
            ('hotel_id', '=', main_hotel),
            ('booking_ok', '=', True)])
        ctx = self._context.copy()
        ctx.update({'default_rooms_ids': [(6, 0, rooms.ids)],'default_company_id': main_hotel})

        if len(sheets) > 1:
            view_type = 'tree,form'
            domain = "[('id', 'in', " + str(sheets.ids) + \
                "),('company_id', '='," + \
                str(main_hotel) + ")]"
            sheets.write({'rooms_ids': [(6, 0, rooms.ids)]})
        else:
            sheets.write({'rooms_ids': [(6, 0, rooms.ids)]})
            domain = "[('company_id', '=', " + \
                str(main_hotel) + ")]"
        value = {
            'domain': domain,
            'name': _('Open Room Availability Sheet'),
            'view_type': 'form',
            'view_mode': view_type,
            'res_model': 'room.availability',
            'view_id': False,
            'target': 'main',
            'type': 'ir.actions.act_window',
            'context': ctx
        }
        print(value)
        print(value)
        print(sheets)
        if len(sheets) == 1:
            sheets.write({'rooms_ids': [(6, 0, rooms.ids)]})
            value['res_id'] = sheets.id
        return value
