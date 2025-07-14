# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo.http import request, route, Controller


class RecentlyViewedController(Controller):
    def create_new_record(self, res_id, model, action_name, user_id):
        res = False

        if res_id and model:
            name = request.env[model].sudo().search([('id', '=', int(res_id))], limit=1).display_name and request.env[model].sudo().search([('id', '=', int(res_id))], limit=1).display_name or ""
            res = request.env['os.recently.viewed.record'].sudo().create({
                'name': action_name + '/' + name,
                'res_id': res_id,
                'model': model,
                'user_id': user_id})

        return res
    @route(
        ['/theme/recently/viewed/records'], type='json', auth='public', csrf=False)
    def recently_view_record(self, data):
        if data:
            res_id = data['res_id']
            model = data['model']
            action = data['action']
            user_id = request.env.user.id
            action_id = request.env['ir.actions.act_window'].sudo().search([('id', '=', int(action))], limit=1)
            if action_id:
                action_name = action_id.name
                record_id = request.env['os.recently.viewed.record'].sudo().search([
                    ('res_id', '=', res_id),
                    ('model', '=', model),
                    ('user_id', '=', user_id)], limit=1)

                record_ids = request.env['os.recently.viewed.record'].sudo().search([('user_id', '=', user_id)])
                nb_records = len(record_ids)
                if nb_records == 10:
                    if record_id:
                        record_id.sudo().unlink()
                        self.create_new_record(res_id, model, action_name, user_id)
                    else:
                        record_ids[9].sudo().unlink()
                        self.create_new_record(res_id, model, action_name, user_id)
                else:
                    if record_id:
                        record_id.sudo().unlink()
                        self.create_new_record(res_id, model, action_name, user_id)
                    else:
                        self.create_new_record(res_id, model, action_name, user_id)

        return self._get_recently_record()

    @route([
        '/theme/get/recently/viewed/records'], type='json', auth='public', csrf=False)
    def get_recently_view_record(self, **post):
        return self._get_recently_record()

    def _get_recently_record(self):
        user_id = request.env.user.id
        records = request.env['os.recently.viewed.record'].sudo().search([('user_id', '=', user_id)], order='write_date desc', limit=10)
        records_list = []
        for record in records:
            record_dict = {
                'name': record.name,
                'res_id': record.res_id,
                'model': record.model,
            }
            records_list.append(record_dict)
        return records_list
