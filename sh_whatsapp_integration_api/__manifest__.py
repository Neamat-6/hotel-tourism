# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "All in one WhatsApp Integration-Sales, Purchase, Account and CRM API | WhatsApp Business | Chat API | Whatsapp Chat API Integration",
    "author": "Softhealer Technologies",
    "website": "http://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": "Whatsapp Odoo Connector,whatsup integration API,Invoice To Customer Whatsapp,stock Whatsapp,Sales Whatsapp,Purchase Whatsapp,CRM Whatsapp,Invoice whatsapp,All in one Whatsup Integration,whatsapp integration API,Whatsup Odoo Connector",
    "description": """Nowadays, There is WhatsApp which is a widely used messenger to communicate with customers and it's faster than compares to emails. But in odoo there is no feature to send an order, documentation to your related customers, vendors, and contacts as well. Our this module will help to send message and orders on WhatsApp it sounds quite familiar, right? so what's new in this app? In this app you no need to go on WhatsApp web page, Just one click to send a message or order to your customer. Just get token and instance from 'Chat Api' and configure that in odoo and go for it.""",
    "version": "15.0.5",
    "depends": ['crm', 'sale_management', 'purchase', 'stock'],
    "application": True,
    "data": [
            "data/sale_email_data.xml",
            "security/whatsapp_security.xml",
            "security/ir.model.access.csv",
            "wizard/send_whatsapp_message_view.xml",
            "views/res_partner_views.xml",
            "wizard/send_whasapp_number_view.xml",
            "views/crm_lead_inherit_views.xml",
            "views/sale_order_inherit_view.xml",
            "views/purchase_order_inherit_view.xml",
            "views/customer_invoice_inherit_view.xml",
            "views/customer_delivery_inherit_view.xml",
            "views/res_config_settings.xml",
            "views/res_users_inherit_view.xml",
            "views/account_payment_inherit_view.xml",
            "views/configuration_manager.xml",
            "wizard/qr_code.xml"
    ],
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": 90,
    "currency": "EUR"
}
