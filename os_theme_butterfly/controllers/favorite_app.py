# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo.http import request, route, Controller
from odoo import _


class FavoriteAppController(Controller):

    @route([
        '/theme/get/favorite_app'], type='json', auth='public', csrf=False)
    def get_favorite_app_list(self, **post):
        return self._get_favorite_apps()

    def _get_favorite_apps(self):
        user_id = request.env.user.id
        domain = [('user_id', '=', user_id)]
        records = request.env['os.favorite.app'].search(domain, order="sequence")
        menus_ids = records.mapped('menu_id').ids
        records_list = []
        for record in records:
            record_dict = {
                'id': record.id,
                'name': record.name,
                'menu_id': record.menu_id.id,
                'menu_name': record.menu_id.name,
                'sequence': record.sequence,
                'menus_ids': menus_ids,
            }
            records_list.append(record_dict)
        return records_list

    @route(
        ['/theme/favorite_app/add'], type='json', auth='public', csrf=False)
    def add_favorite_app(self, data):
        user_id = request.env.user.id
        error = ""
        if data and data['name'] and data['menu_id']:
            record_exists = request.env['os.favorite.app'].search([('user_id', '=', user_id), ('menu_id.id', '=', int(data['menu_id']))])
            if not record_exists:
                request.env['os.favorite.app'].create({
                    'name': data['name'],
                    'menu_id': int(data['menu_id']),
                    'sequence': int(data['sequence']),
                    'user_id': user_id})
            else:
                error = _('This favorite app already exists!')

        return [error, self._get_favorite_apps()]

    @route(
        ['/theme/favorite_app/delete'], type='json', auth='public', csrf=False)
    def delete_favorite_app(self, data):
        user_id = request.env.user.id
        if data and data["id"]:
            request.env['os.favorite.app'].search([('id', '=', int(data['id'])), ('user_id', '=', user_id)]).unlink()
        return self._get_favorite_apps()

    @route(
        ['/theme/favorite_app/update'], type='json', auth='public', csrf=False)
    def update_favorite_app(self, data):
        user_id = request.env.user.id
        if data and data['id'] and data['name'] and data['sequence']:
            record = request.env['os.favorite.app'].search([('id', '=', int(data['id'])), ('user_id', '=', user_id)])
            record.write({
                'name': data['name'],
                'sequence': data['sequence'],
            })
        return self._get_favorite_apps()
