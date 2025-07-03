# -*- coding: utf-8 -*-
{
    'name': "HTask Connector",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'account', 'point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/htask_security.xml',
        # 'data/config_data.xml',
        'data/journal_data.xml',
        # 'data/account.account.csv',
        'data/product_data.xml',
        'data/htask.account.type.csv',
        # 'data/htask.account.configuration.csv',
        # 'data/tax_data.xml',
        'data/pos_data.xml',

        # 'data/account_data.xml',
        'data/ir_cron.xml',
        'data/invoice_action_server.xml',
        'wizard/manager_report_wizard.xml',
        'wizard/htask_sync_revenues.xml',
        # 'views/assets.xml',
        'views/view_res_partner.xml',
        'views/manager_report_template.xml',
        'views/manager_report_views.xml',
        'views/revenues_views.xml',
        'views/hotel_folio_views.xml',
        'views/res_config_settings_views.xml',
        'views/account_configuration_views.xml',
        'views/account_journal_view.xml',
        'views/account_account_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            "/htask_connector/static/src/js/room_charge_n.js",
            "/htask_connector/static/src/js/payment_screen.js",
            "/htask_connector/static/src/js/pos_receipt.js",
            "/htask_connector/static/src/css/pos.css",
        ],
        'web.assets_qweb': [
            '/htask_connector/static/src/xml/room_charge.xml',
            '/htask_connector/static/src/xml/account_payment.xml'
        ],
    },
}
