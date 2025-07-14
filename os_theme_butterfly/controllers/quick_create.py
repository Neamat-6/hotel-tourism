# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo.http import request, route, Controller
from odoo import _


class quickCreateController(Controller):

    @route([
        '/theme/get/quick_create'], type='json', auth='public', csrf=False)
    def get_quick_create(self, **post):
        return self._get_quick_create_list()

    def _get_quick_create_list(self):
        user_id = request.env.user.id
        domain = [('user_id', '=', user_id)]
        records = request.env['os.quick.create'].sudo().search(domain, order="sequence")
        models_ids = records.mapped('model').ids
        records_list = []
        for record in records:
            record_dict = {
                'id': record.id,
                'name': record.name,
                'icon': record.icon,
                'model': {
                    "id": record.model.id,
                    "name": record.model.name,
                    "model": record.model.model
                },
                'sequence': record.sequence,
                'models_ids': models_ids,
            }
            records_list.append(record_dict)
        return records_list

    @route(
        ['/theme/quick_create/add'], type='json', auth='public', csrf=False)
    def add_quick_create(self, data):
        user_id = request.env.user.id
        error = ""
        if data and data['name'] and data['model']:
            record_exists = request.env['os.quick.create'].search([('user_id', '=', user_id), ('model.id', '=', int(data['model']))])
            if not record_exists:
                request.env['os.quick.create'].create({
                    'name': data['name'],
                    'model': int(data['model']),
                    'sequence': data['sequence'],
                    'icon': data['icon'],
                    'user_id': user_id})
            else:
                error = _('This Quick Create action already exists!')

        return [error, self._get_quick_create_list()]

    @route(
        ['/theme/quick_create/delete'], type='json', auth='public', csrf=False)
    def delete_quick_create(self, data):
        user_id = request.env.user.id
        if data and data["id"]:
            request.env['os.quick.create'].search([('id', '=', int(data['id'])), ('user_id', '=', user_id)]).unlink()
        return self._get_quick_create_list()

    @route(
        ['/theme/quick_create/update'], type='json', auth='public', csrf=False)
    def update_quick_create(self, data):
        user_id = request.env.user.id
        if data and data['id'] and data['name']:
            record = request.env['os.quick.create'].search([('id', '=', int(data['id'])), ('user_id', '=', user_id)])
            record.write({
                'name': data['name'],
                'sequence': data['sequence'],
                'icon': data['icon'],
            })
        return self._get_quick_create_list()
