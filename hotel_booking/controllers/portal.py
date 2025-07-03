# -*- coding: utf-8 -*-

import binascii

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager


class CustomerPortal(portal.CustomerPortal):

    # Add Booking Values
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        Booking = request.env['hotel.booking']
        if 'booking_count' in counters:
            values['booking_count'] = Booking.search_count(self._prepare_bookings_domain(partner)) \
                if Booking.check_access_rights('read', raise_exception=False) else 0

        return values

    # Bookings Domain
    def _prepare_bookings_domain(self, partner):
        return [
            ('partner_id', 'child_of', [partner.commercial_partner_id.id])
        ]

    # Sort By-s
    def _get_booking_searchbar_sortings(self):
        return {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }

    # All Bookings Page
    @http.route(['/my/bookings', '/my/bookings/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_bookings(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Booking = request.env['hotel.booking']

        domain = self._prepare_bookings_domain(partner)

        searchbar_sortings = self._get_booking_searchbar_sortings()

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        booking_count = Booking.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/bookings",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=booking_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        bookings = Booking.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_bookings_history'] = bookings.ids[:100]

        values.update({
            'date': date_begin,
            'bookings': bookings.sudo(),
            'page_name': 'booking',
            'pager': pager,
            'default_url': '/my/bookings',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("hotel_booking.portal_my_bookings", values)

    # Get Single Booking
    @http.route(['/my/bookings/<int:booking_id>'], type='http', auth="public", website=True)
    def portal_booking_page(self, booking_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            booking_sudo = self._document_check_access('hotel.booking', booking_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=booking_sudo, report_type=report_type, report_ref='hotel_booking.custom_booking', download=download)

        values = {
            'booking': booking_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': booking_sudo.partner_id.id,
            'report_type': 'html',
            'action': request.env.ref('hotel_booking.action_hotel_booking'),
        }
        if booking_sudo.company_id:
            values['res_company'] = booking_sudo.company_id

        history = request.session.get('my_bookings_history', [])
        values.update(get_records_pager(history, booking_sudo))

        return request.render('hotel_booking.booking_portal_template', values)

    # Sign Booking
    @http.route(['/my/bookings/<int:booking_id>/accept'], type='json', auth="public", website=True)
    def portal_booking_sign(self, booking_id, access_token=None, name=None, signature=None):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            booking_sudo = self._document_check_access('hotel.booking', booking_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid booking.')}

        if not booking_sudo.has_to_be_signed():
            return {'error': _('The booking is not in a state requiring customer signature.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            booking_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}
        query_string = '?message=sign_ok'
        return {
            'force_refresh': True,
            'redirect_url': booking_sudo.get_portal_url(query_string=query_string),
        }
