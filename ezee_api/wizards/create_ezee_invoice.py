from odoo import fields, models, api
import requests
import json
from datetime import date
import logging
import traceback
logger = logging.getLogger(__name__)


class CreateEzeeInvoice(models.TransientModel):
    _name = 'create.ezee.invoice'
    _description = 'Create Ezee Invoice'


    def create_partner(self, booked_by, booking_tran, company):
        logger.info('create new partner')
        account_receivable = self.env[
            'account.account'].sudo().search(
            [('ezee_api', '=', True),
             ('user_type_id.type', '=', 'receivable')],
            limit=1)
        account_payable = self.env[
            'account.account'].sudo().search(
            [('ezee_api', '=', True),
             ('user_type_id.type', '=', 'payable')], limit=1)
        partner_name = booking_tran['FirstName'] + " " + booking_tran['LastName']
        partner_vals = {}
        if booked_by != partner_name:
            parent_company = self.env['res.partner'].search([('name', '=', booked_by)], limit=1)
            if not parent_company:
                parent_company = self.env['res.partner'].sudo().create({
                    'name': booked_by,
                    'is_company': True,
                    'property_account_receivable_id': account_receivable.id if account_receivable.exists() else None,
                    'property_account_payable_id': account_payable.id if account_payable.exists() else None,
                })
            logger.info(f'parent_company: {parent_company}')
            partner_vals = {"parent_id": parent_company.id, "type": "contact"}
        partner_vals.update({
            'name': partner_name,
            'mobile': booking_tran['Mobile'],
            'email': booking_tran['Email'],
            'company_id': False,
            'property_account_receivable_id': account_receivable.id if account_receivable.exists() else None,
            'property_account_payable_id': account_payable.id if account_payable.exists() else None,
        })

        logger.info(f'partner_vals: {partner_vals}')
        partner_id = self.env['res.partner'].with_company(company).sudo().create(partner_vals)
        return partner_id

    def button_connect(self):
        try:
            url = "https://hoteltask.hotelgenie.online/api/reservations"
            is_company = False
            branches = self.env['res.branch'].sudo().search([('hotel_code', '!=', False)])
            if not branches:
                branches = self.env['res.company'].sudo().search([('hotel_code', '!=', False)])
                is_company = True
            for branch in branches:
                params = {"hotel_code": branch.hotel_code}
                company = branch if is_company else branch.company_id
                logger.info(f'ezee company: {company}')
                response = requests.get(url, params=params)
                if response.status_code != 200:
                    logger.info(f'Error: {response.status_code}')
                    return
                if not response.content:
                    logger.info(f'Empty response content, cannot decode JSON {response.content}')
                    return
                parent_data = json.loads(response.content)
                # parent_data = self.get_data_list()
                data_list = parent_data.get('data', False)
                logger.info(f'ezee data_list: {data_list}')
                if data_list:
                    for data_item in data_list:
                        operation = data_item.get('operation', False)
                        if operation == 'CHECKOUT':
                            data = data_item.get('data', False)
                            if data:
                                reservations = data.get('Reservations', False)
                                if reservations:
                                    reservation_list = reservations.get('Reservation', False)
                                    if reservation_list:
                                        for reservation in reservation_list:
                                            booking_tran_list = reservation.get('BookingTran', False)
                                            booked_by = reservation.get('BookedBy', False)
                                            logger.info(f'booked_by: {booked_by}')
                                            if booking_tran_list:
                                                for booking_tran in booking_tran_list:
                                                    partner_name = booking_tran['FirstName'] + " " + booking_tran['LastName']
                                                    partner_id = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
                                                    account_receivable = self.env[
                                                        'account.account'].sudo().search(
                                                        [('ezee_api', '=', True), ('user_type_id.type', '=', 'receivable')], limit=1)
                                                    if partner_id:
                                                        logger.info(f'exist partner_id: {partner_id}')
                                                        account_payable = self.env[
                                                            'account.account'].sudo().search(
                                                            [('ezee_api', '=', True), ('user_type_id.type', '=', 'payable')], limit=1)
                                                        if partner_id.parent_id:
                                                            new_partner = partner_id.parent_id
                                                        else:
                                                            new_partner = partner_id
                                                        logger.info(f'new_partner: {new_partner}')
                                                        new_partner = new_partner.with_company(company)
                                                        p_account_receivable = new_partner.property_account_receivable_id
                                                        p_account_payable = new_partner.property_account_payable_id
                                                        if not p_account_receivable or not p_account_payable:
                                                            logger.info(f'not found accounts in exist partner {new_partner}')
                                                            new_partner.sudo().write({
                                                                'property_account_receivable_id': account_receivable.id if account_receivable.exists() else None,
                                                                'property_account_payable_id': account_payable.id if account_payable.exists() else None,
                                                            })
                                                        elif not p_account_receivable.ezee_api or not p_account_payable.ezee_api:
                                                            partner_id = self.create_partner(booked_by, booking_tran, company)
                                                    else:
                                                        partner_id = self.create_partner(booked_by, booking_tran, company)
                                                    # booking_line = booking_line[0]
                                                    room_charge = booking_tran.get('TotalAmountBeforeTax', 0)
                                                    municipality_amount = 0
                                                    tax_details = booking_tran.get('TaxDeatil', False)
                                                    extra_charges = booking_tran.get('ExtraCharge', False)
                                                    if tax_details:
                                                        for tax_detail in tax_details:
                                                            if tax_detail.get('TaxCode', False) == '1':
                                                                municipality_amount += float(tax_detail.get('TaxAmount', 0))
                                                    lines = self.prepare_invoice_lines(room_charge, municipality_amount, extra_charges)
                                                    invoice_journal = self.env['account.journal'].with_company(company).search([('ezee_api', '=', True)],limit=1)
                                                    vals = {
                                                        "partner_id": partner_id.id,
                                                        "invoice_date": date.today(),
                                                        "move_type": "out_invoice",
                                                        "invoice_line_ids": lines,
                                                        "ezee_unique_id": reservation.get('UniqueID', False),
                                                        "is_htask_move": True,
                                                        "branch_id": False if is_company else branch.id,
                                                        "company_id": company.id,
                                                    }
                                                    if invoice_journal:
                                                        vals.update({"journal_id": invoice_journal.id})
                                                    # invoice = self.env['account.move'].sudo().create(vals)
                                                    invoice = self.env['account.move'].sudo().create(vals)
                                                    logger.info(f"ezee_unique_id: {reservation.get('UniqueID', False)}")
                                                    logger.info(f'invoice: {invoice}')
                                                    logger.info(f"invoice journal items account {invoice.line_ids.mapped('account_id')}")
                                                    partner_comp = partner_id.with_company(invoice.company_id)
                                                    logger.info(f'partner_id account: {partner_id.property_account_receivable_id}')
                                                    logger.info(f'partner_id account with comp: {partner_comp.property_account_receivable_id}')
                                                    invoice.line_ids[-1].write({'account_id': account_receivable.id})
                                                    try:
                                                        invoice._post()
                                                    except Exception as e:
                                                        logger.info(f'error post {traceback.format_exc()}')
                                                        logger.info(f'error post with error{e}')
                                                    payment_details = booking_tran.get('PaymentDetail', [])
                                                    if payment_details and float(booking_tran.get('TotalPayment', 0)):
                                                        # search for refund
                                                        refund_payment_details = []
                                                        for payment_detail in payment_details:
                                                            if float(payment_detail.get('amount', 0)) < 0:
                                                                refund_payment_details.append(payment_detail)
                                                        for refund_payment_detail in refund_payment_details:
                                                            for payment_detail in payment_details:
                                                                if float(payment_detail.get('amount', 0)) > 0:
                                                                    if payment_detail.get('method', False) and refund_payment_detail.get('method', False):
                                                                        if float(payment_detail['amount']) >= float(refund_payment_detail['amount']) and payment_detail['method'] == refund_payment_detail['method']:
                                                                            payment_detail.update({
                                                                                'amount': float(payment_detail['amount']) + float(refund_payment_detail['amount'])
                                                                            })
                                                                            if refund_payment_detail in refund_payment_details:
                                                                                refund_payment_details.remove(refund_payment_detail)
                                                        # priority to remove refund amount from amount with same method
                                                        if refund_payment_details:
                                                            for refund_payment_detail in refund_payment_details:
                                                                for payment_detail in payment_details:
                                                                    if float(payment_detail.get('amount', 0)) > 0:
                                                                        if payment_detail.get('method',False) and refund_payment_detail.get('method', False):
                                                                            if float(payment_detail['amount']) >= float(refund_payment_detail['amount']) and payment_detail['method'] != refund_payment_detail['method']:
                                                                                payment_detail.update({
                                                                                    'amount': float(payment_detail['amount']) + float(refund_payment_detail['amount'])
                                                                                })
                                                                                if refund_payment_detail in refund_payment_details:
                                                                                    refund_payment_details.remove(refund_payment_detail)
                                                        for payment_detail in payment_details:
                                                                method = False
                                                                if payment_detail.get('method', False):
                                                                    if payment_detail['method'] == 'Cash':
                                                                        method = 'Cash'
                                                                    elif payment_detail['method'] == 'Credit Card':
                                                                        method = 'Credit Card'
                                                                    elif payment_detail['method'] == 'Debit Card':
                                                                        method = 'Credit Card'
                                                                if method and float(payment_detail.get('amount', 0)) > 0:
                                                                    payment_vals = {
                                                                        'payment_date': invoice.invoice_date,
                                                                        'amount': payment_detail.get( 'amount'),
                                                                    }
                                                                    journal_id = self.env['account.journal'].with_company(company).search([('ezee_journal_type', '=', method)],limit=1)
                                                                    if journal_id:
                                                                        payment_vals.update({'journal_id': journal_id.id})
                                                                    try:
                                                                        logger.info(f'payment_vals: {payment_vals}')
                                                                        payment = self.env['account.payment.register'].with_company(
                                                                            company).with_context(
                                                                            active_model='account.move', active_ids=invoice.ids,
                                                                        ).create(payment_vals)
                                                                        logger.info(f'payment register: {payment}')
                                                                        res = payment.action_create_payments()
                                                                        logger.info(f'payment created: {res}')
                                                                    except Exception as e:
                                                                        logger.info(f'error from button_connect payment: {e}')
                                                        logger.info(f'invoice.amount_residual: {invoice.amount_residual}')
                                                        if invoice.amount_residual == 0.01 and invoice.payment_state in ['in_payment', 'paid', 'partial']:
                                                            logger.info(f'invoice.amount_residual diff: {invoice.amount_residual}')
                                                            payment_vals = {
                                                                'payment_date': invoice.invoice_date,
                                                                'amount': 0.01,
                                                            }
                                                            journal_id = self.env['account.journal'].with_company(company).search([('ezee_journal_type','=', 'difference')],limit=1)
                                                            if journal_id:
                                                                payment_vals.update({'journal_id': journal_id.id})
                                                            payment = self.env['account.payment.register'].with_company(
                                                                company).with_context(
                                                                active_model='account.move', active_ids=invoice.ids,
                                                            ).create(payment_vals)
                                                            payment.action_create_payments()
        except Exception as e:
            logger.info(f'error from button_connect create_ezee_invoice: {traceback.format_exc()} --- {e}')

    def prepare_invoice_lines(self, room_charge, municipality_amount, extra_charges):
        vals = []
        room_charge_product = self.env['product.product'].sudo().search([('room_charge_product', '=', True)], limit=1)
        municipality_product = self.env['product.product'].sudo().search([('municipality_product', '=', True)], limit=1)
        extra_charge_product = self.env['product.product'].sudo().search([('extra_charge_product', '=', True)], limit=1)
        vals.append((0, 0, {
            'product_id': room_charge_product.id,
            'name': room_charge_product.name,
            'quantity': 1,
            'price_unit': room_charge,
            'tax_ids': [(6, 0, room_charge_product.taxes_id.ids)]
        }))
        vals.append((0, 0, {
            'product_id': municipality_product.id,
            'name': municipality_product.name,
            'quantity': 1,
            'price_unit': municipality_amount,
            'tax_ids': [(6, 0, municipality_product.taxes_id.ids)]
        }))
        if extra_charges:
            for extra_charge in extra_charges:
                vals.append((0, 0, {
                    'product_id': extra_charge_product.id,
                    'name': extra_charge_product.name,
                    'quantity': 1,
                    'price_unit': extra_charge.get('AmountAfterTax', 0),
                    'tax_ids': [(6, 0, extra_charge_product.taxes_id.ids)]
                }))
        return vals

    def create_ezee_invoice(self, kw):
        try:
            logger.info('create_ezee_invoice_func %s', kw)
            operation = kw.get('operation', False)
            hotel_code = kw.get('hotel_code')
            company = None
            # branch = None
            # is_company = False
            if hotel_code:
                # branch = self.env['res.branch'].sudo().search([('hotel_code', '=', hotel_code)])
                # if not branch:
                company = self.env['res.company'].sudo().search(
                    [('hotel_code', '=', hotel_code)])
                    # is_company = True
                # company = branch if is_company else branch.company_id
            else:
                self.env['ir.logging'].sudo().create({
                    'type': 'client',
                    'name': 'create_ezee_invoice',
                    'path': 'create_ezee_invoice',
                    'line': 'create_ezee_invoice',
                    'func': 'create_ezee_invoice',
                    'message': kw,
                    'error': 'missing hotel code'
                })
                return {'status': 'success'}
            if not company:
                self.env['ir.logging'].sudo().create({
                    'type': 'client',
                    'name': 'create_ezee_invoice',
                    'path': 'create_ezee_invoice',
                    'line': 'create_ezee_invoice',
                    'func': 'create_ezee_invoice',
                    'message': kw,
                    'error': f'not found company with hotel code {hotel_code}'
                })
                return {'status': 'success'}
            if operation == 'CHECKOUT':
                data = kw.get('data', {})
                if data:
                    reservations = data.get('Reservations', {})
                    reservation_list = reservations.get('Reservation', [])
                    for reservation in reservation_list:
                        booking_tran_list = reservation.get('BookingTran', [])
                        booked_by = reservation.get('BookedBy', False)
                        logger.info(f'booked_by: {booked_by}')
                        for booking_tran in booking_tran_list:
                            partner_name = booking_tran['FirstName'] + " " + \
                                           booking_tran['LastName']
                            partner_id = self.env['res.partner'].search(
                                [('name', '=', partner_name)], limit=1)
                            account_receivable = self.env[
                                'account.account'].sudo().search(
                                [('ezee_api', '=', True), ('user_type_id.type', '=', 'receivable')],
                                limit=1)
                            if partner_id:
                                logger.info(f'exist partner_id: {partner_id}')
                                account_payable = self.env[
                                    'account.account'].sudo().search(
                                    [('ezee_api', '=', True), ('user_type_id.type', '=', 'payable')], limit=1)
                                if partner_id.parent_id:
                                    new_partner = partner_id.parent_id
                                else:
                                    new_partner = partner_id
                                logger.info(f'new_partner: {new_partner}')
                                new_partner = new_partner.with_company(company)
                                p_account_receivable = new_partner.property_account_receivable_id
                                p_account_payable = new_partner.property_account_payable_id
                                if not p_account_receivable or not p_account_payable:
                                    logger.info(
                                        f'not found accounts in exist partner {new_partner}')
                                    new_partner.sudo().write({
                                        'property_account_receivable_id': account_receivable.id if account_receivable.exists() else None,
                                        'property_account_payable_id': account_payable.id if account_payable.exists() else None,
                                    })
                                elif not p_account_receivable.ezee_api or not p_account_payable.ezee_api:
                                    partner_id = self.create_partner(booked_by, booking_tran, company)
                            else:
                                partner_id = self.create_partner(booked_by, booking_tran, company)
                            # booking_line = booking_line[0]
                            room_charge = booking_tran.get('TotalAmountBeforeTax', 0)
                            municipality_amount = 0
                            tax_details = booking_tran.get('TaxDeatil', False)
                            extra_charges = booking_tran.get('ExtraCharge',False)
                            if tax_details:
                                for tax_detail in tax_details:
                                    if tax_detail.get('TaxCode', False) == '1':
                                        municipality_amount += float(
                                            tax_detail.get('TaxAmount', 0))
                            lines = self.prepare_invoice_lines(room_charge,
                                                               municipality_amount,
                                                               extra_charges)
                            logger.info(f'linessssssssss {lines}')
                            invoice_journal = self.env[
                                'account.journal'].with_company(company).search(
                                [('ezee_api', '=', True)], limit=1)
                            vals = {
                                "partner_id": partner_id.id,
                                "invoice_date": date.today(),
                                "move_type": "out_invoice",
                                "invoice_line_ids": lines,
                                "ezee_unique_id": reservation.get('UniqueID',False),
                                "is_htask_move": True,
                                # "branch_id": False if is_company else branch.id,
                                "company_id": company.id,
                            }
                            if invoice_journal:
                                vals.update({"journal_id": invoice_journal.id})
                            # invoice = self.env['account.move'].sudo().create(vals)
                            invoice = self.env['account.move'].sudo().create(vals)
                            logger.info(f"ezee_unique_id: {reservation.get('UniqueID', False)}")
                            logger.info(f'invoice: {invoice}')
                            logger.info(f"invoice journal items account {invoice.line_ids.mapped('account_id')}")
                            partner_comp = partner_id.with_company(invoice.company_id)
                            logger.info(f'partner_id account: {partner_id.property_account_receivable_id}')
                            logger.info(f'partner_id account with comp: {partner_comp.property_account_receivable_id}')
                            invoice.line_ids[-1].write({'account_id': account_receivable.id})
                            try:
                                invoice._post()
                            except Exception as e:
                                logger.info(f'error post {traceback.format_exc()}')
                                logger.info(f'error post with error{e}')
                            payment_details = booking_tran.get('PaymentDetail',[])
                            if payment_details and float(booking_tran.get('TotalPayment', 0)):
                                # search for refund
                                refund_payment_details = []
                                for payment_detail in payment_details:
                                    if float(payment_detail.get('amount',0)) < 0:
                                        refund_payment_details.append(payment_detail)
                                for refund_payment_detail in refund_payment_details:
                                    for payment_detail in payment_details:
                                        if float(payment_detail.get('amount',0)) > 0:
                                            if payment_detail.get('method',False) and refund_payment_detail.get('method', False):
                                                if float(payment_detail['amount']) >= float(refund_payment_detail['amount']) and payment_detail['method'] == refund_payment_detail['method']:
                                                    payment_detail.update({
                                                        'amount': float(payment_detail['amount']) + float(refund_payment_detail['amount'])
                                                    })
                                                    if refund_payment_detail in refund_payment_details:
                                                        refund_payment_details.remove(refund_payment_detail)
                                # priority to remove refund amount from amount with same method
                                if refund_payment_details:
                                    for refund_payment_detail in refund_payment_details:
                                        for payment_detail in payment_details:
                                            if float(payment_detail.get('amount',0)) > 0:
                                                if payment_detail.get('method',False) and refund_payment_detail.get('method', False):
                                                    if float(payment_detail['amount']) >= float(refund_payment_detail['amount']) and payment_detail['method'] != refund_payment_detail['method']:
                                                        payment_detail.update({
                                                            'amount': float(payment_detail['amount']) + float(refund_payment_detail['amount'])
                                                        })
                                                        if refund_payment_detail in refund_payment_details:
                                                            refund_payment_details.remove(
                                                                refund_payment_detail)
                                for payment_detail in payment_details:
                                    method = False
                                    if payment_detail.get('method', False):
                                        if payment_detail['method'] == 'Cash':
                                            method = 'Cash'
                                        elif payment_detail['method'] == 'Credit Card':
                                            method = 'Credit Card'
                                        elif payment_detail['method'] == 'Debit Card':
                                            method = 'Credit Card'
                                    if method and float(
                                            payment_detail.get('amount',0)) > 0:
                                        payment_vals = {
                                            'payment_date': invoice.invoice_date,
                                            'amount': payment_detail.get('amount'),
                                        }
                                        journal_id = self.env[
                                            'account.journal'].with_company(company).search([('ezee_journal_type', '=',method)], limit=1)
                                        if journal_id:
                                            payment_vals.update({'journal_id': journal_id.id})
                                        try:
                                            logger.info(f'payment_vals: {payment_vals}')
                                            payment = self.env[
                                                'account.payment.register'].with_company(
                                                company).with_context(
                                                active_model='account.move',
                                                active_ids=invoice.ids,
                                            ).create(payment_vals)
                                            logger.info(f'payment register: {payment}')
                                            res = payment.action_create_payments()
                                            logger.info(f'payment created: {res}')
                                        except Exception as e:
                                            logger.info(f'error from button_connect payment: {e}')
                                logger.info(f'invoice.amount_residual: {invoice.amount_residual}')
                                if invoice.amount_residual == 0.01 and invoice.payment_state in ['in_payment', 'paid', 'partial']:
                                    logger.info(f'invoice.amount_residual diff: {invoice.amount_residual}')
                                    payment_vals = {
                                        'payment_date': invoice.invoice_date,
                                        'amount': 0.01,
                                    }
                                    journal_id = self.env[
                                        'account.journal'].with_company(company).search([('ezee_journal_type', '=','difference')], limit=1)
                                    if journal_id:
                                        payment_vals.update(
                                            {'journal_id': journal_id.id})
                                    payment = self.env[
                                        'account.payment.register'].with_company(company).with_context(
                                        active_model='account.move',
                                        active_ids=invoice.ids,
                                    ).create(payment_vals)
                                    payment.action_create_payments()
            return {'status': 'success'}
        except Exception as e:
            logger.info(f'create_ezee_invoice {traceback.format_exc()} --- {e}')
            self.env['ir.logging'].sudo().create({
                'type': 'client',
                'name': 'create_ezee_invoice',
                'path': 'create_ezee_invoice',
                'line': 'create_ezee_invoice',
                'func': 'create_ezee_invoice',
                'message': kw,
                'error': traceback.format_exc()
            })
            return {'status': 'success'}

    def get_data_list(self):
        data = {'data': [{"data": {"Reservations": {"Reservation": [{"BookingTran": [
            {"SubBookingId": "3503-2", "TransactionId": "4065200000000022492", "Createdatetime": "2024-12-10 17:39:08",
             "Modifydatetime": "2024-12-10 17:39:08", "Status": "New", "IsConfirmed": "1",
             "CurrentStatus": "Checked Out", "VoucherNo": "", "PackageCode": "4065200000000000003",
             "PackageName": "Room Only", "RateplanCode": "4065200000000000002", "RateplanName": "Quad Room Only",
             "RoomTypeCode": "4065200000000000004", "RoomTypeName": "Quad", "RoomID": "4065200000000000305",
             "RoomName": "917", "Start": "2025-01-29", "End": "2025-02-01", "ArrivalTime": "23:45:52",
             "DepartureTime": "12:46:10", "CurrencyCode": "SAR", "TotalAmountAfterTax": "780.00",
             "TotalAmountBeforeTax": "661.74", "TotalTax": "118.26", "TotalDiscount": "0.00",
             "TotalExtraCharge": "0.00", "TotalPayment": "600.00", "TACommision": "0.00", "Salutation": "Mr.",
             "FirstName": "Golden", "LastName": "Qutoof", "Gender": "Male", "DateOfBirth": "2025-01-08",
             "SpouseDateOfBirth": "", "WeddingAnniversary": "", "Address": "", "City": "", "State": "",
             "Country": "Egypt", "Nationality": "Angola", "Zipcode": "", "Phone": "-", "Mobile": "0549589537",
             "Fax": "-", "Email": "qutufgolden@gmail.com", "RegistrationNo": "", "IdentiyType": "", "IdentityNo": "",
             "ExpiryDate": "", "TransportationMode": "", "Vehicle": "", "PickupDate": "", "PickupTime": "",
             "Source": "Individuals", "Comment": "", "AffiliateName": "", "AffiliateCode": "", "CCLink": "", "CCNo": "",
             "CCType": "", "CCExpiryDate": "", "CardHoldersName": "",
             "TaxDeatil": [{"TaxCode": "1", "TaxName": "Municipality city Tax", "TaxAmount": "5.5100"},
                           {"TaxCode": "1", "TaxName": "Municipality city Tax", "TaxAmount": "5.5100"},
                           {"TaxCode": "1", "TaxName": "Municipality city Tax", "TaxAmount": "5.5100"},
                           {"TaxCode": "2", "TaxName": "Vat", "TaxAmount": "33.9100"},
                           {"TaxCode": "2", "TaxName": "Vat", "TaxAmount": "33.9100"},
                           {"TaxCode": "2", "TaxName": "Vat", "TaxAmount": "33.9100"}],
             "PaymentDetail": [{"amount": "960.0000", "datetime": "2025-01-07 19:31:38", "method": "Cash"},
                               {"amount": "-360.0000", "datetime": "2025-01-25 19:41:08", "method": "Cash"}],
             "RentalInfo": [{"RoomID": "4065200000000000305", "RoomName": "917", "EffectiveDate": "2025-01-29",
                             "PackageCode": "4065200000000000003", "PackageName": "Room Only",
                             "RoomTypeCode": "4065200000000000004", "RoomTypeName": "Quad", "Adult": "4", "Child": "0",
                             "RentPreTax": "220.58", "Rent": "260.00", "Discount": "0.00"},
                            {"RoomID": "4065200000000000305", "RoomName": "917", "EffectiveDate": "2025-01-30",
                             "PackageCode": "4065200000000000003", "PackageName": "Room Only",
                             "RoomTypeCode": "4065200000000000004", "RoomTypeName": "Quad", "Adult": "3", "Child": "0",
                             "RentPreTax": "220.58", "Rent": "260.00", "Discount": "0.00"},
                            {"RoomID": "4065200000000000305", "RoomName": "917", "EffectiveDate": "2025-01-31",
                             "PackageCode": "4065200000000000003", "PackageName": "Room Only",
                             "RoomTypeCode": "4065200000000000004", "RoomTypeName": "Quad", "Adult": "3", "Child": "0",
                             "RentPreTax": "220.58", "Rent": "260.00", "Discount": "0.00"}]}], "LocationId": "40652",
                                                                     "UniqueID": "3503", "BookedBy": "Individuals",
                                                                     "Salutation": "Mr.", "FirstName": "Golden",
                                                                     "LastName": "Qutoof", "Gender": "Male",
                                                                     "Address": "", "City": "", "State": "",
                                                                     "Country": "Egypt", "Zipcode": "", "Phone": "-",
                                                                     "Mobile": "0549589537", "Fax": "-",
                                                                     "Email": "qutufgolden@gmail.com",
                                                                     "RegistrationNo": "", "Source": "Individuals",
                                                                     "PaymentMethod": "Cash",
                                                                     "IsChannelBooking": "1"}]}}, "hotel_code": "45299",
                          "operation": "CHECKOUT"}]}
        return data
