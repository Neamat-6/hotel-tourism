import base64
import json
import requests

from odoo import http, api
from odoo.http import request
import logging
import traceback
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.parser import parse

logger = logging.getLogger(__name__)


class HotelGuestOrder(http.Controller):

    def get_uid(self, headers):
        uid = False
        if headers and headers.get('HTTP_AUTHORIZATION'):
            parts = headers['HTTP_AUTHORIZATION'].split(" ")
            if len(parts) == 2:
                try:
                    decoded = base64.b64decode(parts[1]).decode('utf-8')
                    username, password = decoded.split(":")
                    request.session.authenticate(request.cr.dbname, username, password)
                    uid = request.session.uid
                except Exception:
                    # authentication failed or malformed header
                    return False
        return uid

    def check_pilgrim_id(self, pilgrim_id):
        """
        Verify that a partner with this pilgrim_id exists.
        Returns {"status":"success","company_id": <int>} if found,
        or {"status":"failure","error": "..."} otherwise.
        """
        try:
            pilgrim = request.env['res.partner'].sudo().search(
                [('pilgrim_id', '=', pilgrim_id)], limit=1
            )
            if not pilgrim:
                return {"status": "failure", "error": "Pilgrim not found"}
            company = pilgrim.company_id or request.env.company
            return {"status": "success", "company_id": company.id}
        except Exception as e:
            logger.error("check_pilgrim_id error:\n%s", traceback.format_exc())
            return {"status": "failure", "error": str(e)}

    def get_orders_data(self, orders):
        data = []
        for order in orders:
            data.append({
                'id': order.id,
                'name': order.name,
                'guest': {"id": order.partner_id.id, "name": order.partner_id.name},
                'state': order.state,
                'date_order': order.date_order.strftime("%Y-%m-%d %H:%M:%SZ") if order.date_order else "",
                'end_date_order': order.end_date_order.strftime("%Y-%m-%d %H:%M:%SZ") if order.end_date_order else "",
                'actual_start_time': order.actual_start_time.strftime("%Y-%m-%d %H:%M:%SZ") if order.actual_start_time else "",
                'actual_end_time': order.actual_end_time.strftime("%Y-%m-%d %H:%M:%SZ") if order.actual_end_time else "",
                'paid_status': order.paid_status,
                'employee': {"id": order.user_id.id, "name": order.user_id.name},
                'company_id': {"id": order.company_id.id, "name": order.company_id.name},
                'categ_id': {"id": order.categ_id.id, "name": order.categ_id.name},
                'amount_untaxed': order.amount_untaxed,
                'amount_tax': order.amount_tax,
                'amount_total': order.amount_total,
                'note': order.note or '',
                'lines': [{
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'categ_id': line.categ_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'price_subtotal': line.price_subtotal,
                    'price_tax': line.price_tax,
                    'price_total': line.price_total,
                    'tax_id': [{
                        'name': tax.name,
                        'id': tax.id,
                        'included': tax.price_include,
                        'amount': tax.amount
                    } for tax in line.tax_id],
                } for line in order.order_line]
            })
        return data

    @http.route('/user/login/', auth='public', type='json', methods=['GET'], csrf=False)
    def user_login(self):
        uid = self.get_uid(request.httprequest.headers.environ)
        device_token = request.httprequest.headers.get('device_token')
        if uid:
            if device_token:
                request.env['res.users'].sudo().browse(uid).write({'device_token': device_token})
            return {"status": "success", "user": uid}
        return {"status": "failure", "error": "Authentication failed"}

    @http.route('/pilgrim/login/', auth='public', type='json', methods=['GET'], csrf=False)
    def pilgrim_login(self, pilgrim_id):
        logger.info(f'pilgrim_login {pilgrim_id}')
        login = self.check_pilgrim_id(pilgrim_id)
        if login.get('status') != 'success':
            return login

        pilgrim = request.env['res.partner'].sudo().search(
            [('pilgrim_id', '=', pilgrim_id)], limit=1
        )
        if not pilgrim:
            return {"status": "failure", "error": "Pilgrim not found"}

        return {
            "status": "success",
            "company_id": login['company_id'],
            "pilgrim": {
                "id": pilgrim.id,
                "name": pilgrim.name,
            }
        }


    @http.route('/api/categories', auth='public', type='json', methods=['GET'], csrf=False)
    def get_categories(self, pilgrim_id=None):
        try:
            logger.info(f'get_categories {request.httprequest.headers.environ}')
            uid = request.httprequest.headers.get('uid')
            if pilgrim_id:
                login = self.check_pilgrim_id(pilgrim_id)
                if login.get('status') != 'success':
                    return login
                categories = request.env['product.category'].sudo().search([])
            else:
                if not uid:
                    return {"status": "failure", "error": "Authentication failed"}
                user_obj = request.env['res.users'].sudo().browse(uid)
                if user_obj.has_group('hotel_guest_order.group_guest_order_superadmin'):
                    categories = request.env['product.category'].sudo().search([])
                else:
                    categories = user_obj.categ_ids
            data = [{'id': c.id, 'name': c.name} for c in categories]
            return {"status": "success", "data": data}
        except Exception:
            logger.error(f'get_categories error:\n{traceback.format_exc()}')
            return {"status": "failure", "error": traceback.format_exc()}

    @http.route('/api/services', auth='public', type='json', methods=['GET'], csrf=False)
    def get_services(self, pilgrim_id=None):
        try:
            logger.info(f'get_services {request.httprequest.headers.environ}')
            uid = request.httprequest.headers.get('uid')
            if pilgrim_id:
                login = self.check_pilgrim_id(pilgrim_id)
                if login.get('status') != 'success':
                    return login
                products = request.env['product.template'].sudo().search([('is_orderable', '=', True)])
            else:
                if not uid:
                    return {"status": "failure", "error": "Authentication failed"}
                user_obj = request.env['res.users'].sudo().browse(uid)
                if user_obj.has_group('hotel_guest_order.group_guest_order_superadmin'):
                    products = request.env['product.template'].sudo().search([('is_orderable', '=', True)])
                else:
                    cat_ids = user_obj.categ_ids.ids
                    products = request.env['product.template'].sudo().search([('categ_id', 'in', cat_ids),('is_orderable', '=', True)])
            data = [{
                'id': p.id,
                'name': p.name,
                'period': p.period,
                'from_hour': p.from_hour,
                'to_hour': p.to_hour,
                'categ_id': {'id': p.categ_id.id, 'name': p.categ_id.name}
            } for p in products]
            return {"status": "success", "data": data}
        except Exception:
            logger.error(f'get_services error:\n{traceback.format_exc()}')
            return {"status": "failure", "error": traceback.format_exc()}

    @http.route(
        '/api/services/<int:category_id>',
        auth='public', type='json', methods=['GET'], csrf=False
    )
    def get_services_by_categ(self, category_id, pilgrim_id=None):
        try:
            logger.info(f'get_services_by_categ {category_id}')
            uid = request.httprequest.headers.get('uid')
            if pilgrim_id:
                login = self.check_pilgrim_id(pilgrim_id)
                if login.get('status') != 'success':
                    return login
            elif not uid:
                return {"status": "failure", "error": "Authentication failed"}
            products = request.env['product.template'].sudo().search([('categ_id', '=', category_id)])
            data = [{
                'id': p.id,
                'name': p.name,
                'period': p.period,
                'from_hour': p.from_hour,
                'to_hour': p.to_hour,
                'categ_id': {'id': p.categ_id.id, 'name': p.categ_id.name}
            } for p in products]
            return {"status": "success", "data": data}
        except Exception:
            logger.error(f'get_services_by_categ error:\n{traceback.format_exc()}')
            return {"status": "failure", "error": traceback.format_exc()}

    @http.route('/api/get_orders', auth='public', type='json', methods=['GET'], csrf=False)
    def get_orders(self, pilgrim_id=None):
        try:
            logger.info(f'get_orders {request.httprequest.headers.environ}')
            uid = request.httprequest.headers.get('uid')
            if pilgrim_id:
                login = self.check_pilgrim_id(pilgrim_id)
                if login.get('status') != 'success':
                    return login
                partner = request.env['res.partner'].sudo().search(
                    [('pilgrim_id', '=', pilgrim_id)], limit=1
                )
                orders = request.env['guest.order'].sudo().search([('partner_id', '=', partner.id)])
            else:
                if not uid:
                    return {"status": "failure", "error": "Authentication failed"}
                orders = request.env['guest.order'].with_user(uid).search([])
            data = self.get_orders_data(orders)
            return {"status": "success", "data": data}
        except Exception:
            logger.error(f'get_orders error:\n{traceback.format_exc()}')
            return {"status": "failure", "error": traceback.format_exc()}

    @http.route('/api/update_order_status', auth='public', type='json', methods=['POST'], csrf=False)
    def update_order_status(self, order_id, state):
        try:
            uid = request.httprequest.headers.get('uid')
            if not uid:
                return {"status": "failure", "error": "Authentication failed"}
            order = request.env['guest.order'].with_user(uid).browse(order_id)
            if not order:
                return {"status": "failure", "error": "Order not found"}
            order.with_user(uid).write({'state': state})
            return {"status": "success", "order": order_id}
        except Exception:
            logger.error(f'update_order_status error:\n{traceback.format_exc()}')
            return {"status": "failure", "error": traceback.format_exc()}

    @http.route('/api/update_order_employee', auth='public', type='json', methods=['POST'], csrf=False)
    def update_order_employee(self, order_id, employee):
        try:
            uid = request.httprequest.headers.get('uid')
            if not uid:
                return {"status": "failure", "error": "Authentication failed"}
            order = request.env['guest.order'].with_user(uid).browse(order_id)
            if not order:
                return {"status": "failure", "error": "Order not found"}
            order.with_user(uid).write({'user_id': employee})
            return {"status": "success", "order": order_id}
        except Exception:
            logger.error(f'update_order_employee error:\n{traceback.format_exc()}')
            return {"status": "failure", "error": traceback.format_exc()}

    @http.route('/api/create_order/', auth='public', type='json', methods=['POST'], csrf=False)
    def create_order(self, **rec):
        try:
            logger.info(f'create_order payload: {rec}')
            pilgrim_id = rec.get('pilgrim_id')
            if not pilgrim_id:
                return {"status": "failure", "error": "Please send pilgrim_id in payload"}
            login = self.check_pilgrim_id(pilgrim_id)
            if login.get('status') != 'success':
                return login
            company_id = login['company_id']
            pilgrim = request.env['res.partner'].sudo().search(
                [('pilgrim_id', '=', pilgrim_id)], limit=1
            )
            # Determine category from first line item if present
            lines = rec.get('lines') or []
            category = False
            if lines:
                # ensure product_id is an integer
                first_pid = int(lines[0].get('product_id'))
                first_product = request.env['product.template'].sudo().browse(first_pid)
                category = first_product.categ_id

            new_order = request.env["guest.order"].sudo().create({
                'partner_id': pilgrim.id,
                'company_id': company_id,
                'categ_id': category.id if category else False,
            })

            for line in lines:
                # again, cast to int
                pid = int(line.get('product_id'))
                prod = request.env['product.template'].sudo().browse(pid)
                order_line = request.env["guest.order.line"].sudo().create({
                    'order_id': new_order.id,
                    'product_id': prod.product_variant_id.id,
                    'product_uom_qty': line.get('product_uom_qty'),
                    'location': line.get('location'),
                    'company_id': company_id,
                })
                order_line._onchange_product_id()

            return {"status": "success", "order": new_order.id}

        except Exception:
            logger.error(f'create_order error:\n{traceback.format_exc()}')
            return {"status": "failure", "error": traceback.format_exc()}
    def get_employees(self):
        uid = request.httprequest.headers.get('uid')
        if not uid:
            return {"status": "failure", "error": "Authentication failed"}
        employee_group = request.env.ref('hotel_guest_order.group_guest_order_user').id
        admin_groups = [
            request.env.ref('hotel_guest_order.group_guest_order_admin').id,
            request.env.ref('hotel_guest_order.group_guest_order_superadmin').id,
        ]
        employees = request.env['res.users'].sudo().search([
            ('groups_id', '=', employee_group),
            ('groups_id', 'not in', admin_groups)
        ])
        data = [{
            'id': emp.id,
            'name': emp.name,
            'categ_ids': [{'id': c.id, 'name': c.name} for c in emp.categ_ids],
            'company_ids': [{'id': c.id, 'name': c.name} for c in emp.company_ids],
        } for emp in employees]
        return {"status": "success", "data": data}
