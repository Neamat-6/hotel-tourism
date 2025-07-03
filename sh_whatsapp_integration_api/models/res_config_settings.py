# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    order_information_in_message = fields.Boolean(
        "Order Information in message? ON Sale Order", default=True)
    order_product_detail_in_message = fields.Boolean(
        "Order Product details in message? ON Sale Order", default=True)
    signature = fields.Boolean("Signature? ON Sale Order", default=True)
    display_in_message = fields.Boolean(
        "Display in Chatter Message? ON Sale Order", default=True)
    send_pdf_in_message = fields.Boolean(
        "Send Report URL in message? ON Sale Order", default=True)

    purchase_order_information_in_message = fields.Boolean(
        "Order Information in message? ON Purchase Order", default=True)
    purchase_product_detail_in_message = fields.Boolean(
        "Order Product details in message? ON Purchase Order", default=True)
    purchase_signature = fields.Boolean("Signature? ON Purchase Order", default=True)
    purchase_display_in_message = fields.Boolean(
        "Display in Chatter Message? ON Purchase Order", default=True)
    po_send_pdf_in_message = fields.Boolean(
        "Send Report URL in message? ON Purchase Order", default=True)

    invoice_order_information_in_message = fields.Boolean(
        "Order Information in message? ON Invoice", default=True)
    invoice_product_detail_in_message = fields.Boolean(
        "Order Product details in message? ON Invoice", default=True)
    invoice_signature = fields.Boolean("Signature? ON Invoice", default=True)
    invoice_display_in_message = fields.Boolean(
        "Display in Chatter Message? ON Invoice", default=True)
    inv_send_pdf_in_message = fields.Boolean(
        "Send Report URL in message? ON Invoice", default=True)

    inventory_information_in_message = fields.Boolean(
        "Order Information in message? ON Inventory", default=True)
    inventory_signature = fields.Boolean("Signature? ON Inventory", default=True)
    inventory_display_in_message = fields.Boolean(
        "Display in Chatter Message? ON Inventory", default=True)
    stock_send_pdf_in_message = fields.Boolean(
        "Send Report URL in message? ON Inventory", default=True)

    crm_lead_signature = fields.Boolean("Signature? On Crm", default=True)
    crm_lead_display_in_message = fields.Boolean(
        "Display in Chatter Message? On Crm", default=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    order_information_in_message = fields.Boolean(
        related="company_id.order_information_in_message", string="Order Information in message? On sale Order", readonly=False)
    order_product_detail_in_message = fields.Boolean(
        related="company_id.order_product_detail_in_message", string="Order Product details in message? On sale Order", readonly=False)
    signature = fields.Boolean(
        related="company_id.signature", string="Signature? On sale Order", readonly=False)
    display_in_message = fields.Boolean(
        related="company_id.display_in_message", string="Display in Chatter Message? On sale Order", readonly=False)
    send_pdf_in_message = fields.Boolean(
        related="company_id.send_pdf_in_message", string="Send Report URL in message? On sale Order", readonly=False)

    purchase_order_information_in_message = fields.Boolean(
        related="company_id.purchase_order_information_in_message", string="Order Information in message? On Purchase Order", readonly=False)
    purchase_product_detail_in_message = fields.Boolean(
        related="company_id.purchase_product_detail_in_message", string="Order Product details in message? On Purchase Order", readonly=False)
    purchase_signature = fields.Boolean(
        related="company_id.purchase_signature", string="Signature? On Purchase Order", readonly=False)
    purchase_display_in_message = fields.Boolean(
        related="company_id.purchase_display_in_message", string="Display in Chatter Message? On Purchase Order", readonly=False)
    po_send_pdf_in_message = fields.Boolean(
        related="company_id.po_send_pdf_in_message", string="Send Report URL in message? On Purchase Order", readonly=False)

    invoice_order_information_in_message = fields.Boolean(
        related="company_id.invoice_order_information_in_message", string="Order Information in message? On Invoice", readonly=False)
    invoice_product_detail_in_message = fields.Boolean(
        related="company_id.invoice_product_detail_in_message", string="Order Product details in message? On Invoice", readonly=False)
    invoice_signature = fields.Boolean(
        related="company_id.invoice_signature", string="Signature? On Invoice", readonly=False)
    invoice_display_in_message = fields.Boolean(
        related="company_id.invoice_display_in_message", string="Display in Chatter Message? On Invoice", readonly=False)
    inv_send_pdf_in_message = fields.Boolean(
        related="company_id.inv_send_pdf_in_message", string="Send Report URL in message? On Invoice", readonly=False)

    inventory_information_in_message = fields.Boolean(
        related="company_id.inventory_information_in_message", string="Order Information in message? On Inventory", readonly=False)
    inventory_signature = fields.Boolean(
        related="company_id.inventory_signature", string="Signature? On Inventory", readonly=False)
    inventory_display_in_message = fields.Boolean(
        related="company_id.inventory_display_in_message", string="Display in Chatter Message? On Inventory", readonly=False)
    stock_send_pdf_in_message = fields.Boolean(
        related="company_id.stock_send_pdf_in_message", string="Send Report URL in message? On Inventory", readonly=False)

    crm_lead_display_in_message = fields.Boolean(
        related="company_id.crm_lead_display_in_message", string="Display in Chatter Message? On Crm", readonly=False)
    crm_lead_signature = fields.Boolean(
        related="company_id.crm_lead_signature", string="Signature? On Crm", readonly=False)
