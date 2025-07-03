# -*- coding: utf-8 -*-
{
    'name': "Hotel Booking Folio",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': 'Hotels Task',
    'website': "https://www.hotelstask.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'hotel_booking', 'report_xlsx', 'report_xlsx_helper','point_of_sale'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'data/data.xml',
        'data/server_actions.xml',
        'views/hotel.xml',
        'views/hotel_booking.xml',
        'views/booking_folio.xml',
        'views/account_tax.xml',
        'views/account_move.xml',
        'views/hotel_room.xml',
        'views/hotel_services.xml',
        'wizards/booking_payment_register.xml',
        'wizards/night_audit.xml',
        'wizards/folio_report.xml',
        'wizards/folio_filter.xml',
        'wizards/folio_service.xml',
        'wizards/folio_amend_stay.xml',
        'wizards/folio_change_room.xml',
        'wizards/booking_filter_view.xml',
        'wizards/booking_apply_discount.xml',
        'wizards/booking_group_action.xml',
        'wizards/folio_room_charge.xml',
        'wizards/daily_revenue.xml',
        'wizards/daily_revenue_by_room_type.xml',
        'wizards/daily_revenue_by_rate_plan.xml',
        'wizards/daily_revenue_by_tax.xml',
        'wizards/revenue_summary.xml',
        'wizards/trial_balance_wizard.xml',
        'wizards/booking_refund_payment.xml',
        'wizards/warn_wizard.xml',
        'wizards/daily_tax_view.xml',
        'wizards/room_type_availability_report.xml',
        'reports/folio_report.xml',
        'reports/folio_filter.xml',
        'reports/trial_balance_wizard.xml',
        'reports/folio_xlsx.xml',
        'reports/daily_revenue.xml',
        'reports/revenue_summary.xml',
        'reports/daily_revenue_xlsx.xml',
        'reports/room_type_availability_xlsx.xml',
        'reports/room_type_availability.xml',
        'reports/reservation_report.xml',
        'reports/electronic_invoice_template.xml',
        'reports/cashier_summary_report.xml',
        'data/hotel_room_charge_data.xml',
        'views/hotel_room_charge.xml',
        'wizards/room_charge_wizard.xml',
        'wizards/guest_ledger.xml',
        'reports/guest_ledger_report.xml',
        'wizards/hotel_manager_report.xml',
        'reports/manager_report.xml',
        'wizards/cashier_summary_wizard.xml',
        'wizards/room_availability.xml',
        'reports/room_availability_report.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'hotel_booking_folio/static/src/js/folio_filter_widget.js',
            'hotel_booking_folio/static/src/js/group_action_widget.js',
        ],

        'web.assets_qweb': [
            'hotel_booking_folio/static/src/xml/folio_filter_widget.xml',
            'hotel_booking_folio/static/src/xml/group_action_widget.xml',
        ],
    },
}
