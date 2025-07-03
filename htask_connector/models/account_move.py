import logging
import json
import csv
import io
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

move_required = ['currency_id', 'date', 'journal_id', 'name', 'state', 'type']
moveline_required = ['move_id']

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

GUEST_FIELDS = {
    "name": "reference5",  # partner_id.name
    "id_type": "reference17",  # partner_id.id_type
    "id_no": "reference18",  # partner_id.id_no
    "email": "reference19",  # partner_id.email
    "full_addr": "reference20",  # partner_id.full_addr
    "phone": "reference21",  # partner_id.phone
    "mobile": "reference21",  # partner_id.phone
}

REC = {  # account.move (Journal Entry)
    "htask_id_external": "record_id",
    "date": "record_date",
    "check_in_date": "reference1",
    "check_out_date": "reference2",
    "reservation_no": "reference3",
    "folio_no": "reference4",
    "invoice_no": "reference8",
    "voucher_no": "reference10",
    "room_no": "reference13",
    "room_type": "reference14",
    "rate_type": "reference15",
    "market_code": "reference16",
    "source_name": "reference7",
}

LINE = {  # account.move.line (Journal Item)
    "htask_id_external": "detail_record_id",
    "date": "detail_record_date",

    "htask_id_external": "reference_id",  # account_id.id
    "name": "reference13",  # account_id.name
    # "name": "charge_name", # name of journal item // product_id.name (service)?
}


class HTaskRevenue(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "abstract.htask.model"]

    _htask_type = "revenue"

    # check_in_date = fields.Date(string='Check In Date')
    # check_out_date = fields.Date(string='Check Out Date')
    # reservation_no = fields.Char(string='Reservation No.')
    folio_no = fields.Char(string='Folio No.')

    is_htask_move = fields.Boolean(string='Is Htask Move')
    folio_id = fields.Many2one('hotel.folio', string='Folio')
    room_no = fields.Char(string='Room No.')
    room_type = fields.Char(string='Room Type')
    rate_type = fields.Char(string='Rate Type')
    market_code = fields.Char(string='Market Code')
    source_name = fields.Char(string='Source')

    invoice_no = fields.Char(string='Invoice No.')
    htask_payment_type = fields.Char(string='Payment Type')
    htask_payment_name = fields.Char(string='Payment Name')
    htask_payment_ids = fields.Many2many('account.payment', string='Htask Payments')

    # voucher_no = fields.Char(string='Voucher No.')
    def update_account_move_folio(self):
        for record in self:
            for line in record.line_ids:
                line.folio_id = record.folio_id.id

    def retrieve_create_guest(self, revenue_rec):
        # Check if folio already created from bill, update guest record
        Partner = self.env["res.partner"]
        res = {
            "is_guest": True,
            "company_id": self.env.company.id,
            "branch_id": self.env.user.branch_id.id,
            "name": "",  # partner_id.name
            "id_type": "",  # partner_id.id_type
            "id_no": "",  # partner_id.id_no
            "email": "",  # partner_id.email
            "full_addr": "",  # partner_id.full_addr
            "phone": "",  # partner_id.phone
            "mobile": "",  # partner_id.phone
        }
        for k, v in GUEST_FIELDS.items():
            if revenue_rec.get(v, False):
                res.update({k: revenue_rec[v]})

        guest_id = False
        if res:
            folio_id = self.env['hotel.folio'].search(
                [('name', '=', str(revenue_rec['reference4'])), ('branch_id', '=', self.env.user.branch_id.id)])
            if folio_id and folio_id.partner_id.name == revenue_rec['reference5'] and not folio_id.move_ids:
                guest_id = folio_id.partner_id
                guest_id.write(res)
            else:
                guest_id = Partner.search([
                    ('name', '=', res.get('name')),
                    ('id_no', '=', res.get('id_no')),
                    ('id_type', '=', res.get('id_type')),
                    ('full_addr', '=', res.get('full_addr')),
                    ('email', '=', res.get('email')), '|',
                    ('phone', '=', res.get('phone')),
                    ('mobile', '=', res.get('mobile')),
                    ('branch_id', '=', self.env.user.branch_id.id),
                ], limit=1)

                # Ignore revenue if guest has no name TODO REVENUE IGNORED
                if not res.get('name', ''):
                    # Get last number for unnamed guests
                    idx = 1
                    all_guest_ids = self.env['res.partner'].search(
                        [('is_guest', '=', True), ('name', 'ilike', 'Unnamed')])
                    if all_guest_ids:
                        noname_index = all_guest_ids.mapped(lambda g: int(g.name.split('_')[1]))
                        idx = max(noname_index) + 1
                    res['name'] = 'Unnamed_' + str(idx)

                    if guest_id:
                        guest_id.write({'name': res['name']})

                if not guest_id:
                    guest_id = Partner.create(res)

        return guest_id

    def retrieve_create_folio(self, revenue_rec, guest_id):
        Folio = self.env['hotel.folio']
        folio_no = str(revenue_rec['reference4'])
        # Check if folio already exists, create new one if not
        folio_id = Folio.search([('name', '=', folio_no), ('branch_id', '=', self.env.user.branch_id.id)])
        folio_data = {
            "name": folio_no,
            "partner_id": guest_id.id if guest_id else False,
            "checkin_date": revenue_rec["reference1"],
            "checkout_date": revenue_rec["reference2"],
            "reservation_no": revenue_rec["reference3"],
            "invoice_no": revenue_rec["reference8"],
            "voucher_no": revenue_rec["reference10"],
            "source_name": revenue_rec["reference7"],
            'branch_id': self.env.user.branch_id.id,
        }
        # update folio created from bill
        if folio_id:
            folio_id.sudo().write(folio_data)
        else:
            folio_id = Folio.sudo().create(folio_data)

        return folio_id

    # Custom Section
    @api.model
    def get_conversion_dict(self):
        res = super().get_conversion_dict()
        res.update({
            "htask_id_external": "record_id",
            "date": "record_date",
            "folio_no": "reference4",
            "invoice_no": "reference8",
            "source_name": "reference7",
            "room_no": "reference13",
            "room_type": "reference14",
            "rate_type": "reference15",
            "market_code": "reference16",
        })
        return res

    @api.model
    def get_odoo_data_from_htask(self, data):
        res = super().get_odoo_data_from_htask(data)
        # get data of related move lines
        res.update({
            "move_type": "out_invoice",
        })
        return res

    def get_line_keys_for_comparison(self, reference):
        ref_id = ref_val = ''
        if reference in [2, 3, 5]:  # Extra Charges, Taxes, Discount
            ref_id = 'sub_ref2_id'
            ref_val = 'sub_ref2_value'
        elif reference == 1:  # Room Revenue
            ref_id = 'sub_ref5_id'
            ref_val = 'sub_ref5_value'
        elif reference in [4, 7]:  # Adjustment, Folio Transfer
            ref_id = 'sub_ref1_id'
            ref_val = 'sub_ref1_value'
        return ref_id, ref_val

    def _retrieve_htask_account(self, line, res_accounts):
        # Decide what to compare
        ref_id, ref_val = self.get_line_keys_for_comparison(line['reference_id'])

        if ref_id and ref_val:
            for rec in res_accounts:
                if rec['header'] == line['reference_name'] and rec['headerid'] == str(line['reference_id']) and rec[
                    'descriptiontypeunkid'] == str(line[ref_id]) and rec['descriptionunkid'] == str(line[ref_val]):
                    return rec

        return False

    def _retrieve_create_htask_tax(self, acc_id, description, amount):
        AccountTax = self.env['account.tax']
        tax_id = AccountTax.search([
            ('name', '=', description + '_' + str(amount)),
            ('amount', '=', amount),
            ('company_id', '=', self.env.company.id)
        ])
        if not tax_id:
            put_first = amount < 3.0
            tax_id = AccountTax.create({
                'name': description + '_' + str(amount),
                'description': description,
                'amount': amount,
                'company_id': self.env.company.id,
                'sequence': 1 if put_first else 100,
                'type_tax_use': 'sale',
                'include_base_amount': put_first,
                'invoice_repartition_line_ids': [(5, 0, 0),
                                                 (0, 0, {
                                                     'factor_percent': 100,
                                                     'repartition_type': 'base',
                                                 }),
                                                 (0, 0, {
                                                     'factor_percent': 100,
                                                     'repartition_type': 'tax',
                                                     'account_id': acc_id,
                                                 })],
                'refund_repartition_line_ids': [(5, 0, 0),
                                                (0, 0, {
                                                    'factor_percent': 100,
                                                    'repartition_type': 'base',
                                                }),
                                                (0, 0, {
                                                    'factor_percent': 100,
                                                    'repartition_type': 'tax',
                                                    'account_id': acc_id,
                                                })]
            })
        return tax_id.id if tax_id else False

    def check_bill_date(self, date):
        """
        validate the fetched bill date
        """
        try:
            bill_date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
            unmapped = False
        except ValueError:
            bill_date = datetime.today()
            unmapped = True

        return [bill_date, unmapped]

    def button_sync_revenues(self, start_date=False, end_date=False):
        htask_revenue = self.get_htask_connector(self._htask_type)
        htask_bill = self.get_htask_connector('bill')
        inwards_payments = self.get_htask_connector('inwards')
        incidental_invoices = self.get_htask_connector('inwards')
        Folio = self.env['hotel.folio']

        if not start_date and not end_date:
            date_now = fields.Datetime.now()

            start_date_obj = date_now
            start_date = start_date_obj.strftime("%Y-%m-%d")

            end_date_obj = date_now
            end_date = end_date_obj.strftime("%Y-%m-%d")

        # Sync Bills
        bill_request_data = {
            "authcode": htask_revenue.auth_code,
            "hotel_code": htask_revenue.hotel_code,
            "fromdate": start_date,
            "todate": end_date,
        }

        bills = htask_bill.get_post(arguments={}, data=bill_request_data)
        bills = bills.decode('utf-8')
        reader = csv.DictReader(io.StringIO(str(bills)))

        bills = []
        for row in reader:
            bills.append(row)

        # Create folios and folio detail lines from bills
        for bill_rec in bills:
            # ================= Create/Get Partner =============================
            if '. ' in bill_rec['Guest Name']:
                guest_name = bill_rec['Guest Name'].split('. ')[1].strip()
            else:
                guest_name = bill_rec['Guest Name'].strip()
            Partner = self.env["res.partner"]
            res = {
                "is_guest": True,
                "name": guest_name,  # partner_id.name
                "phone": bill_rec['Phone Number'],  # partner_id.phone
                "mobile": bill_rec['Mobile Number'],  # partner_id.phone
            }
            if bill_rec['Type'] == 'City Ledger' and bill_rec['Particular']:
                company_id = Partner.search([('name', '=', bill_rec['Particular']),
                                             ('branch_id', '=', self.env.user.branch_id.id)], limit=1)
                if company_id:
                    res['parent_id'] = company_id.id
                else:
                    company_id = Partner.create(
                        {'name': bill_rec['Particular'], 'company_type': 'company', 'is_guest': True,
                         "branch_id": self.env.user.branch_id.id})
                    res['parent_id'] = company_id.id

            guest_id = Partner.search([
                ('name', '=', res.get('name')), '|',
                ('phone', '=', res.get('phone')),
                ('mobile', '=', res.get('mobile')),
                ('branch_id', '=', self.env.user.branch_id.id),
            ], limit=1)

            # Ignore revenue if guest has no name TODO REVENUE IGNORED
            if not res.get('name'):
                # Get last number for unnamed guests
                idx = 1
                all_guest_ids = Partner.search([
                    ('is_guest', '=', True),
                    ('branch_id', '=', self.env.user.branch_id.id),
                    ('name', 'ilike', 'Unnamed')
                ])
                if all_guest_ids:
                    noname_index = all_guest_ids.mapped(lambda g: int(g.name.split('_')[1]))
                    idx = max(noname_index) + 1
                res['name'] = 'Unnamed_' + str(idx)

                if guest_id:
                    guest_id.write({'name': res['name']})
                if guest_id and bill_rec['Type'] == 'City Ledger' and bill_rec['Particular']:
                    company_id = Partner.search([('name', '=', bill_rec['Particular']),
                                                 ('branch_id', '=', self.env.user.branch_id.id)])
                    if company_id:
                        guest_id.parent_id = company_id.id

            if not guest_id:
                guest_id = Partner.create(res)

            # =================================================================

            # ================== Create/Get Folio =============================
            folio_id = Folio.search(
                [('name', '=', bill_rec['Folio No']), ('branch_id', '=', self.env.user.branch_id.id)])
            if not folio_id:
                folio_id = Folio.create({
                    "name": bill_rec['Folio No'],
                    "partner_id": guest_id.id if guest_id else False,
                    "invoice_no": bill_rec["Invoice Number"],
                    "voucher_no": bill_rec["VoucherNo/ReceiptNo"],
                    'branch_id': self.env.user.branch_id.id,
                })

            # Check this line is payment or not
            is_payment = True
            if bill_rec['Type'] in ('Room Charges', 'Extra Charges', 'Adjustments') or (float(
                    bill_rec['Total']) >= 0.0 and 'Refund' not in bill_rec['Particular']):
                is_payment = False

            bill_date_lst = self.check_bill_date(bill_rec['Date'])

            # Create folio detail line if does not exist
            detail_id = self.env['hotel.folio.detail'].search(
                ['|', ('unique_id', '=', bill_rec['Unique id']), '&', ('ref_no', '=', bill_rec['VoucherNo/ReceiptNo']),
                 ('ref_no', 'not in', [False, '', ' '])])  # that is for exclude ref_no which is empty
            if detail_id:
                detail_id.write({
                    'qty': float(bill_rec['Qty']) if bill_rec['Qty'] else 1.0,
                    'amount_subtotal': float(bill_rec['Amount']),
                    'ref_no': bill_rec['VoucherNo/ReceiptNo'],
                    'bill_date': bill_rec['Date'] if int(bill_rec['Date'].split('-')[0]) > 0 else False,
                    # due to invalid date format,
                    'unmapped': bill_date_lst[1],
                    'name': bill_rec['Particular'],
                    'type': bill_rec['Type'],
                    'is_payment': is_payment
                })

            else:
                self.env['hotel.folio.detail'].create({
                    'folio_id': folio_id.id,
                    'unique_id': bill_rec['Unique id'],
                    'name': bill_rec['Particular'],
                    'type': bill_rec['Type'],
                    'qty': float(bill_rec['Qty']) if bill_rec['Qty'] else 1.0,
                    'amount_subtotal': float(bill_rec['Amount']),
                    'ref_no': bill_rec['VoucherNo/ReceiptNo'],
                    'bill_date': bill_rec['Date'] if int(bill_rec['Date'].split('-')[0]) > 0 else False,
                    # due to invalid date format
                    'unmapped': bill_date_lst[1],
                    'is_payment': is_payment,
                    'branch_id': self.env.user.branch_id.id,
                })

            # =========================================================================

        # Sync ischeckout Revenues
        request_params = {
            "auth_code": htask_revenue.auth_code,
            "hotel_code": htask_revenue.hotel_code,
            "fromdate": start_date,
            "todate": end_date,
            "ischeckout": "true",
            "requestfor": "XERO_GET_TRANSACTION_DATA"
        }

        checkout_revenues = htask_revenue.get_post(arguments={}, data=request_params)

        # Sync is not checkout Revenues
        request_params = {
            "auth_code": htask_revenue.auth_code,
            "hotel_code": htask_revenue.hotel_code,
            "fromdate": start_date,
            "todate": end_date,
            "ischeckout": "false",
            "requestfor": "XERO_GET_TRANSACTION_DATA"
        }

        without_checkout_revenues = htask_revenue.get_post(arguments={}, data=request_params)
        all_revenues = []
        msg = ''

        is_checkout_list = isinstance(checkout_revenues, list)
        without_checkout_list = isinstance(without_checkout_revenues, list)

        if is_checkout_list:
            all_revenues.extend(checkout_revenues)

        if without_checkout_list:
            all_revenues.extend(without_checkout_revenues)

        if (not is_checkout_list and checkout_revenues.get('msg')) or (
                not without_checkout_list and without_checkout_revenues.get('msg')):
            msg += checkout_revenues['msg'] + " while trying to fetch checkout revenues\n"

        for revenue_rec in all_revenues:
            # Ignore revenue if total = 0.0 TODO REVENUE IGNORED
            if not float(revenue_rec.get('total_amount')):
                continue

            guest_id = self.retrieve_create_guest(revenue_rec)

            # Create new folio or retrieve if exists
            folio_id = self.retrieve_create_folio(revenue_rec, guest_id)

            # to add the taxes in folio
            if 'detail' in revenue_rec:
                for line in revenue_rec['detail']:
                    if line['reference_name'] != 'Taxes':
                        continue

                    # get exist tax folio detail or create new one
                    tax_folio_detail = self.env['hotel.folio.detail'].search(
                        [('unique_id', '=', line['detail_record_id']), ('name', '=', line['charge_name'])])

                    if tax_folio_detail:
                        tax_folio_detail.write({
                            'amount_subtotal': line['amount'],
                        })

                    else:
                        self.env['hotel.folio.detail'].create({
                            'folio_id': folio_id.id,
                            'name': line['charge_name'],
                            'type': 'Taxes',
                            'qty': 1.0,
                            'amount_subtotal': line['amount'],
                            'bill_date': line['detail_record_date'],
                            'unique_id': line['detail_record_id'],
                            'branch_id': self.env.user.branch_id.id,
                        })

        # ================================ City ledger payments ================================
        request_params = {
            "auth_code": inwards_payments.auth_code,
            "hotel_code": inwards_payments.hotel_code,
            "fromdate": start_date,
            "todate": end_date,
            "requestfor": "XERO_GET_RECEIPT_DATA"
        }

        inwards_payments = inwards_payments.get_post(arguments={}, data=request_params)
        for payment in inwards_payments['data']:
            if payment['type'] == 'Received From Cityledger':
                for line in payment['data']:
                    detail_id = self.env['hotel.folio.detail'].search([('unique_id', '=', line['tranId'])])
                    if detail_id:
                        detail_id.write({
                            'qty': 1.0,
                            'amount_subtotal': -1 * float(line['gross_amount']),
                            'ref_no': line['reference1'],
                            'bill_date': line['tran_datetime'] if int(
                                line['tran_datetime'].split('-')[0]) > 0 else False,
                            'name': line['reference2'],
                            'type': 'Received From Cityledger',
                            'is_payment': True,
                            'is_city_payment': True
                        })

                    else:
                        self.env['hotel.folio.detail'].create({
                            'unique_id': line['tranId'],
                            'qty': 1.0,
                            'amount_subtotal': -1 * float(line['gross_amount']),
                            'ref_no': line['reference1'],
                            'bill_date': line['tran_datetime'] if int(
                                line['tran_datetime'].split('-')[0]) > 0 else False,
                            'name': line['reference2'],
                            'type': 'Received From Cityledger',
                            'is_payment': True,
                            'is_city_payment': True,
                            'branch_id': self.env.user.branch_id.id,
                        })

            if payment['type'] == 'Advance Deposit':
                for line in payment['data']:
                    folio_id = self.env['hotel.folio'].search([('name', '=', line['reference5'])], limit=1)
                    detail_id = self.env['hotel.folio.detail'].search(
                        ['|', ('unique_id', '=', line['tranId']), '&', ('ref_no', '=', line['reference1']),
                         ('ref_no', 'not in', [False, '', ' '])])  # that is for exclude ref_no which is empty
                    if detail_id:
                        detail_id.write({
                            'folio_id': folio_id.id,
                            'qty': 1.0,
                            'amount_subtotal': -1 * float(line['gross_amount']),
                            'ref_no': line['reference1'],
                            'bill_date': line['tran_datetime'] if int(
                                line['tran_datetime'].split('-')[0]) > 0 else False,
                            'name': line['reference14'],
                            'type': 'Advance Deposit',
                            'is_payment': True,
                        })

                    else:
                        self.env['hotel.folio.detail'].create({
                            'folio_id': folio_id.id,
                            'unique_id': line['tranId'],
                            'qty': 1.0,
                            'amount_subtotal': -1 * float(line['gross_amount']),
                            'ref_no': line['reference1'],
                            'bill_date': line['tran_datetime'] if int(
                                line['tran_datetime'].split('-')[0]) > 0 else False,
                            'name': line['reference14'],
                            'type': 'Advance Deposit',
                            'is_payment': True,
                            'branch_id': self.env.user.branch_id.id,
                        })

        # =============================== INCIDENTAL INVOICE =============================

        request_params = {
            "auth_code": incidental_invoices.auth_code,
            "hotel_code": incidental_invoices.hotel_code,
            "fromdate": start_date,
            "todate": end_date,
            "requestfor": "XERO_INCIDENTAL_INVOICE"
        }

        incidental_invoices_list = incidental_invoices.get_post(arguments={}, data=request_params)
        if incidental_invoices_list.get('status', '') == 'Success':
            for incidental in incidental_invoices_list.get('data', []):
                if incidental.get('type', '') == 'Incidental Invoice':
                    for data in incidental.get('data', []):
                        for line in data.get('detail', []):
                            detail_id = self.env['hotel.folio.detail'].search(
                                [('unique_id', '=', line['detailId'])])
                            if detail_id:
                                detail_id.write({
                                    'qty': 1.0,
                                    'ref_no': data['tranId'],
                                    'amount_subtotal': -1 * float(line['amount']) if line[
                                                                                         'tran_type'] == 'Dr' else float(
                                        line['amount']),
                                    'bill_date': data['tran_datetime'] if int(
                                        data['tran_datetime'].split('-')[0]) > 0 else False,
                                    'name': line['reference_value'],
                                    'type': 'Incidental Invoice',
                                    'is_payment': True if line['tran_type'] == 'Dr' else False,
                                })

                            else:
                                self.env['hotel.folio.detail'].create({
                                    'unique_id': line['detailId'],
                                    'qty': 1.0,
                                    'ref_no': data['tranId'],
                                    'amount_subtotal': -1 * float(line['amount']) if line[
                                                                                         'tran_type'] == 'Dr' else float(
                                        line['amount']),
                                    'bill_date': data['tran_datetime'] if int(
                                        data['tran_datetime'].split('-')[0]) > 0 else False,
                                    'name': line['reference_value'],
                                    'type': 'Incidental Invoice',
                                    'is_payment': True if line['tran_type'] == 'Dr' else False,
                                    'branch_id': self.env.user.branch_id.id,
                                })

    def full_update(self, start_date, end_date):
        self.button_sync_revenues(start_date, end_date)

    @api.model
    def cron_update_revenue_list(self):
        self.button_sync_revenues()

        return True


class HTaskRevenueLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "abstract.htask.model"]

    _htask_type = "revenue_line"

    balance_abs = fields.Monetary(compute='_compute_balance_abs', string='Balance Abs', store=True)
    is_htask_line = fields.Boolean(compute='_compute_is_htask_line', string='Is Htask Line', store=True)

    @api.depends('move_id.is_htask_move', 'account_id.user_type_id')
    def _compute_is_htask_line(self):
        acc_types = [self.env.ref('account.data_account_type_receivable').id,
                     self.env.ref('account.data_account_type_payable').id]
        for rec in self:
            rec.is_htask_line = rec.move_id.is_htask_move and rec.account_id.user_type_id.id not in acc_types

    @api.depends('balance')
    def _compute_balance_abs(self):
        for rec in self:
            rec.balance_abs = abs(rec.balance)

    @api.model
    def get_odoo_data_from_htask(self, data):
        res = super().get_odoo_data_from_htask(data)
        return res

    @api.model
    def get_conversion_dict(self):
        res = super().get_conversion_dict()
        res.update({
            "htask_id_external": "detail_record_id",
            "date": "detail_record_date",
            "name": "charge_name",  # name of journal item // product_id.name (service)?
        })
        return res


class AccountPayment(models.Model):
    _inherit = "account.payment"

    htask_payment_type = fields.Char(string='Payment Type')
    htask_payment_name = fields.Char(string='Payment Name')

    def update_htask_payment(self):
        for record in self:
            for line in record.line_ids:
                line.folio_id = record.folio_id.id


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"
    # _name = "account.payment.register"

    htask_payment_type = fields.Char(string='Payment Type')
    htask_payment_name = fields.Char(string='Payment Name')
    amount = fields.Float(string='Amount')

    # def _create_payment_vals_from_wizard(self):
    #     payment_vals = {
    #         'date': self.payment_date,
    #         'amount': self.amount,
    #         'payment_type': self.payment_type,
    #         'partner_type': self.partner_type,
    #         'ref': self.communication,
    #         'journal_id': self.journal_id.id,
    #         'currency_id': self.currency_id.id,
    #         'partner_id': self.partner_id.id,
    #         'partner_bank_id': self.partner_bank_id.id,
    #         'payment_method_line_id': self.payment_method_line_id.id,
    #         'destination_account_id': self.line_ids[0].account_id.id
    #     }
    #
    #     if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
    #         payment_vals['write_off_line_vals'] = {
    #             'name': self.writeoff_label,
    #             'amount': self.payment_difference,
    #             'account_id': self.writeoff_account_id.id,
    #         }
    #     return payment_vals

    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices/bills to pay. In case of multiple
            documents, they need to be grouped by partner, bank, journal and
            currency.
        :return: The payment values as a dictionary.
        '''

        if self.htask_payment_type:
            amount = self.amount
        else:
            amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id,
                                                                         self.journal_id, self.payment_date)
        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': " ".join(i.ref or i.name for i in invoices),
            'reconciled_invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': ('inbound' if amount > 0 else 'outbound'),
            'amount': abs(amount),
            'currency_id': invoices[0].currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type],
            'partner_bank_account_id': invoices[0].invoice_partner_bank_id.id,
            'htask_payment_type': self.htask_payment_type,
            'htask_payment_name': self.htask_payment_name
        }

        return values
