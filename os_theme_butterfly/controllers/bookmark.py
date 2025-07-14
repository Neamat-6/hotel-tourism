# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo.http import request, route, Controller
from odoo import _


class BookmarkController(Controller):

    # Bookmark
    @route(
        ['/theme/bookmark/save'], type='json', auth='public', csrf=False)
    def save_bookmark(self, data):
        action = "create"
        if data and data['name'] and data['icon'] and data['type'] and data['link']:
            user_id = request.env.user.id
            record_exists = request.env['os.bookmark'].search([('user_id', '=', user_id), ('link', '=', data['link'])])
            if not record_exists:
                request.env['os.bookmark'].create({
                    'name': data['name'],
                    'description': data['description'],
                    'icon': data['icon'],
                    'type': data['type'],
                    'link': data['link'],
                    'user_id': user_id})
            else:
                record_exists.unlink()
                action = "delete"

        return [action, self._get_bookmarks()]

    @route([
        '/theme/get/bookmark'], type='json', auth='public', csrf=False)
    def get_bookmark_list(self, **post):
        return self._get_bookmarks()

    def _get_bookmarks(self):
        user_id = request.env.user.id
        domain = [('user_id', '=', user_id)]
        records = request.env['os.bookmark'].search(domain, order="sequence")
        records_list = []
        for record in records:
            record_dict = {
                'id': record.id,
                'name': record.name,
                'description': record.description,
                'icon': record.icon,
                'type': record.type,
                'link': record.link,
                'sequence': record.sequence,
            }
            records_list.append(record_dict)
        return records_list

    @route(
        ['/theme/bookmark/delete'], type='json', auth='public', csrf=False)
    def delete_bookmark(self, data):
        user_id = request.env.user.id
        if data and data["id"]:
            request.env['os.bookmark'].search([('id', '=', int(data['id'])), ('user_id', '=', user_id)]).unlink()
        return self._get_bookmarks()

    @route(
        ['/theme/bookmark/update'], type='json', auth='public', csrf=False)
    def update_bookmark(self, data):
        user_id = request.env.user.id
        if data and data['id'] and data['name'] and data['icon']:
            record = request.env['os.bookmark'].search([('id', '=', int(data['id'])), ('user_id', '=', user_id)])
            record.write({
                'name': data['name'],
                'description': data['description'],
                'icon': data['icon'],
                'sequence': data['sequence'],
            })
        return self._get_bookmarks()

    @route(
        ['/theme/bookmark/add'], type='json', auth='public', csrf=False)
    def add_bookmark(self, data):
        user_id = request.env.user.id
        error = ""
        if data and data['name'] and data['icon'] and data['type'] and data['link']:
            record_exists = request.env['os.bookmark'].search([('user_id', '=', user_id), ('link', '=', data['link'])])
            if not record_exists:
                request.env['os.bookmark'].create({
                    'name': data['name'],
                    'description': data['description'],
                    'icon': data['icon'],
                    'type': data['type'],
                    'link': data['link'],
                    'sequence': data['sequence'],
                    'user_id': user_id})
            else:
                error = _('A Bookmark with this link already exists!')

        return [error, self._get_bookmarks()]
