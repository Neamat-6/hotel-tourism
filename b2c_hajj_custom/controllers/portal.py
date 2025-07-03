# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from collections import OrderedDict
from datetime import datetime
import re
from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, Response
from odoo.tools import image_process
from odoo.tools.translate import _
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
import werkzeug.utils
import json
import logging
import time
_logger = logging.getLogger(__name__)


class BookingPackagePortal(portal.CustomerPortal):


    @http.route(['/my/chats'], type='http', auth="user", website=True)
    def portal_chats(self, **kw):
        partner = request.env.user.partner_id
        channel = request.env['mail.channel'].sudo().search([
            ('channel_type', '=', 'chat'),
            ('channel_partner_ids', 'in', [partner.id])
        ], limit=1)
        return request.render("b2c_hajj_custom.portal_chat_page", {
            'channel': channel
        })

    @http.route(['/my/chat/send'], type='http', auth='user', website=True, csrf=True)
    def portal_chat_send(self, channel_id=None, message=None, **kw):
        if not channel_id:
            # Choose who to chat with — example: Admin (you can change the ID)
            current_partner = request.env.user.partner_id
            package = request.env['booking.package'].sudo().search([('partner_ids', '=', current_partner.id)], limit=1)
            if package:
                admin_partner = package.create_uid.sudo().partner_id
            else:
                admin_partner = request.env.ref('base.user_admin').sudo().partner_id
            channel = request.env['mail.channel'].sudo().create({
                'name': f'Booking Chat - {current_partner.name}',
                'channel_type': 'chat',
                'channel_partner_ids': [(4, current_partner.id)],
            })
            channel.sudo().write({
                'channel_partner_ids': [(4, admin_partner.id)]
            })
        else:
            channel = request.env['mail.channel'].sudo().browse(int(channel_id))
        if message:
            channel.sudo().message_post(
                body=message,
                author_id=request.env.user.partner_id.id,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )
        return request.redirect('/my/chats')


    # @http.route('/my/package/update_main_member', type='http', auth="user", methods=['POST'],
    #             website=True)
    # def update_main_members(self, **post):
    #     Partner = request.env['res.partner'].sudo()
    #     form = request.httprequest.form  # Get full form data
    #     checkbox_fields = [
    #         'is_hastened', 'tarwiyah', 'ziarat_al_rawdah', 'tawaf_al_qudum',
    #         'jamarat_day1', 'jamarat_day2', 'jamarat_day3', 'jamarat_day4',
    #         'tawaf_al_ifada_sai', 'tawaf_al_wada'
    #     ]
    #
    #     guest_data = {}
    #
    #     for key in form.keys():
    #         if '_' not in key:
    #             continue
    #         field_name, partner_id_str = key.rsplit('_', 1)
    #         if not partner_id_str.isdigit():
    #             continue
    #         partner_id = int(partner_id_str)
    #         values = form.getlist(key)
    #
    #         if field_name in checkbox_fields:
    #             guest_data.setdefault(partner_id, {})[field_name] = 'true' in values
    #         elif field_name == 'madinah_actual_room_number':
    #             guest_data.setdefault(partner_id, {})['madinah_actual_room_number'] = values[0] if values else ''
    #
    #     try:
    #         for partner_id, values in guest_data.items():
    #             guest = Partner.browse(partner_id)
    #             print(f"Updating Partner {partner_id} with:", values)
    #             guest.write(values)
    #
    #         request.session['portal_message'] = "Guests updated successfully!"
    #     except Exception as e:
    #         request.session['portal_message'] = f"Error updating guests: {str(e)}"
    #
    #     return request.redirect(
    #         f"{request.httprequest.referrer}?t={time.time()}#pilgrims-information"
    #         if request.httprequest.referrer else "/my/package#pilgrims-information"
    #     )

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        BookingPackage = request.env['booking.package']
        if 'package_count' in counters:
            values['package_count'] = BookingPackage.search_count([]) if BookingPackage.check_access_rights('read', raise_exception=False) else 0
        return values

    def _render_booking_package_portal(self, template, page, date_begin, date_end, sortby, filterby, domain, searchbar_filters, default_filter, url, history, page_name, key):
        values = self._prepare_portal_layout_values()
        BookingPackage = request.env['booking.package']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
        }
        # default sort
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if searchbar_filters:
            # default filter
            if not filterby:
                filterby = default_filter
            domain += searchbar_filters[filterby]['domain']

        # count for pager
        count = BookingPackage.search_count(domain)

        # make pager
        pager = portal_pager(
            url=url,
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=count,
            page=page,
            step=self._items_per_page
        )

        # search the purchase orders to display, according to the pager data
        packages = BookingPackage.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session[history] = packages.ids[:100]

        values.update({
            'date': date_begin,
            key: packages,
            'page_name': page_name,
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': url,
        })
        print("Packages retrieved: %s", packages.ids)
        return request.render(template, values)

    def _booking_package_get_page_view_values(self, package, access_token, **kwargs):
        #
        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(request.env['ir.http']._placeholder())
            return image_process(b64source, size=(48, 48))

        values = {
            'package': package,
            'resize_to_48': resize_to_48,
            'report_type': 'html',
        }
        return self._get_page_view_values(package, access_token, values, '', False, **kwargs)

    @http.route(['/my/package', '/my/package/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_booking_packages(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        return self._render_booking_package_portal(
            "b2c_hajj_custom.portal_my_booking_packages",
            page, date_begin, date_end, sortby, filterby,
            [],
            {
                'all': {'label': _('All'), 'domain': [('state', 'in', ['draft', 'confirmed'])]},
                'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
                'confirmed': {'label': _('Confirmed'), 'domain': [('state', '=', 'confirmed')]},
            },
            'all',
            "/my/package",
            'my_purchases_history',
            'package',
            'packages'
        )

    @http.route(['/my/package/<int:package_id>'], type='http', auth="public", website=True)
    def portal_my_booking_package(self, package_id=None, access_token=None, **kw):
        try:
            package_sudo = self._document_check_access('booking.package', package_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._booking_package_get_page_view_values(package_sudo, access_token, **kw)
        values['partner_id'] = request.env.user.partner_id
        values['guide'] = request.env.user.partner_id.is_guide
        values['guide_id'] = request.env.user.partner_id.tour_guide_id
        # values['partner_ids'] = package_sudo.partner_ids
        values['partner_ids'] = request.env['res.partner'].sudo().search([('tour_guide_id', '=', request.env.user.partner_id.id)])

        print("Package retrieved: %s", package_sudo.id)
        print("values: %s", values)
        return request.render("b2c_hajj_custom.portal_my_booking_package", values)


    @http.route(['/my/update_saudi_mobile'], type='http', auth='user', website=True, methods=['POST'])
    def update_saudi_mobile_submit(self, **post):
        partner = request.env.user.partner_id
        saudi_mobile = post.get('saudi_mobile')
        try:
            partner.sudo().write({'saudi_mobile': saudi_mobile if saudi_mobile else None})
            request.session['portal_message'] = "Saudi Mobile updated successfully!"
        except Exception as e:
            request.session['portal_message'] = f"Error updating Mobile: {str(e)}"
        return request.redirect(
            f"{request.httprequest.referrer}?t={time.time()}#informations"
            if request.httprequest.referrer else "/my/package#informations"
        )
        

    @http.route(['/my/hotel/<string:key>'], type='http', auth="user", website=True)
    def portal_hotel_details(self, key, **kw):
        return request.render(
            "b2c_hajj_custom.portal_hotel_details",
            {'hotel_key': key}
        )

    @http.route(['/my/assistant'], type='http', auth="user", website=True)
    def portal_assistant(self, **kw):
        return request.render("b2c_hajj_custom.portal_assistant_page", {})

    @http.route('/my/pilgrim_tasks', type='http', auth="user", website=True)
    def portal_pilgrim_tasks(self, **kw):
        partner = request.env.user.partner_id
        pilgrims = request.env['res.partner'].sudo().search([
            ('tour_guide_id','=',partner.id),
            ('is_guide','=',False),
        ])
        return request.render("b2c_hajj_custom.portal_pilgrim_tasks_page", {
            'pilgrims': pilgrims,
        })



    @http.route('/my/pilgrim_tasks/update', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_pilgrim_tasks_update(self, **post):
        partner = request.env.user.partner_id
        if not partner.is_guide:
            return request.redirect('/my')
        pilgrims = request.env['res.partner'].sudo().search([
            ('tour_guide_id','=',partner.id),
            ('is_guide','=',False),
        ])
        boolean_fields = [
            'is_hastened','tarwiyah','ziarat_al_rawdah','tawaf_al_qudum',
            'jamarat_day1','jamarat_day2','jamarat_day3','jamarat_day4',
            'tawaf_al_ifada_sai','tawaf_al_wada'
        ]
        for pilgrim in pilgrims:
            vals = {}
            for field in boolean_fields:
                key = f"{field}_{pilgrim.id}"
                vals[field] = key in post
            room_key = f"makkah_actual_room_number{pilgrim.id}"
            if room_key in post:
                vals['makkah_actual_room_number'] = post.get(room_key).strip()
            pilgrim.sudo().write(vals)
        request.session['portal_message'] = "Tasks updated successfully!"
        return request.redirect('/my/pilgrim_tasks')


    @http.route('/my/activities', type='http', auth="user", website=True)
    def portal_activities(self, **kw):
        partner = request.env.user.partner_id
        package = partner.package_id
        if not package:
            return request.redirect('/my')
        Activity = request.env['booking.package.activity.line'].sudo()
        lines = Activity.search([('package_id', '=', package.id)], order='date,location')
        from collections import defaultdict
        by_loc = defaultdict(list)
        for ln in lines:
            by_loc[ln.location].append(ln)
        return request.render("b2c_hajj_custom.portal_activities_page", {
            'package': package,
            'activities_by_location': dict(by_loc),
        })
        
    
    @http.route(['/my/qibla'], type='http', auth="user", website=True)
    def portal_qibla(self, **kw):
        """
        Renders the Qibla‐direction page.
        """
        return request.render("b2c_hajj_custom.portal_qibla_page", {})
    
    
    @http.route(['/my/quran'], type='http', auth="user", website=True)
    def portal_quran(self, **kw):
        """
        Renders the Qur’ān‐reader page with a language dropdown and an iframe.
        """
        return request.render("b2c_hajj_custom.portal_quran_page", {})
