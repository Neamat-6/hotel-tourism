# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo.http import request, route, Controller


class TodoController(Controller):

    @route(
        ['/theme/todo/save'], type='json', auth='public', csrf=False)
    def save_todo(self, data):
        error = False
        if data and data['name']:
            name = data['name']
            user_id = request.env.user.id
            record_exists = request.env['os.todo'].search([('user_id', '=', user_id), ('name', '=', name)])
            if not record_exists:
                request.env['os.todo'].create({
                    'name': name,
                    'sequence': request.env['os.todo'].search_count([('user_id', '=', user_id)]) + 1,
                    'user_id': user_id})
            else:
                error = True
        return [error, self._get_todo_list()]

    @route([
        '/theme/get/todo'], type='json', auth='public', csrf=False)
    def get_todo(self, type=None, **post):
        return self._get_todo_list(type)

    def _get_todo_list(self, type=None):
        user_id = request.env.user.id
        domain = [('user_id', '=', user_id)]
        if type and type == "pending":
            domain = [('user_id', '=', user_id), ('is_done', '=', False)]
        if type and type == "completed":
            domain = [('user_id', '=', user_id), ('is_done', '=', True)]
        records = request.env['os.todo'].search(domain, order="sequence")
        res = []
        records_list = []
        there_is_completed = False
        for record in records:
            if record.is_done:
                there_is_completed = True
            record_dict = {
                'id': record.id,
                'name': record.name,
                'is_done': record.is_done,
                'sequence': record.sequence,
            }
            records_list.append(record_dict)
        there_is_completed = there_is_completed and len(records) > 1
        res.append(there_is_completed)
        res.append(records_list)
        return res

    @route(
        ['/theme/todo/toggle/done'], type='json', auth='public', csrf=False)
    def toggle_done_todo(self, data):
        if data:
            is_done = data['is_done']
            id = data['id']
            user_id = request.env.user.id
            record = request.env['os.todo'].search([('id', '=', int(id)), ('user_id', '=', user_id)])
            record.write({
                'is_done': is_done,
            })
        return self._get_todo_list()

    @route(
        ['/theme/todo/delete'], type='json', auth='public', csrf=False)
    def delete_todo(self, data):
        if data:
            action = data['action']
            user_id = request.env.user.id
            if action == "completed":
                request.env['os.todo'].search([('is_done', '=', True), ('user_id', '=', user_id)]).unlink()
            if action == "one" and data['id']:
                request.env['os.todo'].search([('id', '=', int(data['id'])), ('user_id', '=', user_id)]).unlink()
            elif action == "all":
                request.env['os.todo'].search([('user_id', '=', user_id)]).unlink()
        return self._get_todo_list()

    @route(
        ['/theme/todo/edit'], type='json', auth='public', csrf=False)
    def edit_todo(self, data):
        if data:
            id = data['id']
            name = data['name']
            user_id = request.env.user.id
            record = request.env['os.todo'].search([('user_id', '=', user_id), ('id', '=', int(id))])
            if record.name != name:
                record.write({
                    'name': name,
                })
        return self._get_todo_list()
