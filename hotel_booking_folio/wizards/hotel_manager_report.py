from odoo import fields, models, api, _
import toolz as T
import toolz.curried as TC

class ManagerReport(models.TransientModel):
    _name = 'hotel.manager.report'
    _description = 'Manager Report'

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    date = fields.Date(required=True)
    ptd = fields.Date(string='PTD', compute='compute_dates', store=True)
    ytd = fields.Date(string='YTD', compute='compute_dates', store=True)
    # room charge
    room_charge_line_ids = fields.One2many('room.charge.manager.report', 'wizard_id')
    room_charge_date_total = fields.Float(compute='compute_room_charge_date_total', store=True)
    room_charge_ptd_total = fields.Float(compute='compute_room_charge_ptd_total', store=True)
    room_charge_ytd_total = fields.Float(compute='compute_room_charge_ytd_total', store=True)
    room_charge_tax_date_total = fields.Float(compute='compute_room_charge_date_total', store=True)
    room_charge_tax_ptd_total = fields.Float(compute='compute_room_charge_ptd_total', store=True)
    room_charge_tax_ytd_total = fields.Float(compute='compute_room_charge_ytd_total', store=True)
    # extra charge
    extra_charge_line_ids = fields.One2many('extra.charge.manager.report', 'wizard_id')
    extra_charge_date_total = fields.Float(compute='compute_extra_charge_date_total', store=True)
    extra_charge_ptd_total = fields.Float(compute='compute_extra_charge_ptd_total', store=True)
    extra_charge_ytd_total = fields.Float(compute='compute_extra_charge_ytd_total', store=True)
    extra_charge_tax_date_total = fields.Float(compute='compute_extra_charge_date_total', store=True)
    extra_charge_tax_ptd_total = fields.Float(compute='compute_extra_charge_ptd_total', store=True)
    extra_charge_tax_ytd_total = fields.Float(compute='compute_extra_charge_ytd_total', store=True)
    # revenue
    total_date_revenue_without_tax = fields.Float(compute='compute_total_date_revenue_without_tax', store=True)
    total_ptd_revenue_without_tax = fields.Float(compute='compute_total_ptd_revenue_without_tax', store=True)
    total_ytd_revenue_without_tax = fields.Float(compute='compute_total_ytd_revenue_without_tax', store=True)
    total_date_revenue_with_tax = fields.Float(compute='compute_total_date_revenue_with_tax', store=True)
    total_ptd_revenue_with_tax = fields.Float(compute='compute_total_ptd_revenue_with_tax', store=True)
    total_ytd_revenue_with_tax = fields.Float(compute='compute_total_ytd_revenue_with_tax', store=True)
    # payment
    payment_line_ids = fields.One2many('payment.manager.report', 'wizard_id')
    payment_date_total = fields.Float(compute='compute_payment_date_total', store=True)
    payment_ptd_total = fields.Float(compute='compute_payment_ptd_total', store=True)
    payment_ytd_total = fields.Float(compute='compute_payment_ytd_total', store=True)
    # room summary
    room_line_ids = fields.One2many('room.manager.report', 'wizard_id')
    # guest ledger
    total_virtual = fields.Integer(string='Charge Posted')
    total_actual = fields.Integer(string='Total Paid')
    total_balance = fields.Integer()

    def divide(self,numerator,dominator):
        if dominator == 0:
            return 0
        return numerator/dominator

    def _classify_data(self, lines, today_date):
        classified_data = {
            'today':
                T.pipe(
                    lines,
                    TC.filter(lambda line: line['day'] == today_date),
                    list,
                ),
            'month':
                T.pipe(
                    lines,
                    TC.filter(lambda line: line['day'].month == today_date.month if line['day'] else 0),
                    list,
                ),
            'year':
                T.pipe(
                    lines,
                    TC.filter(lambda line: line['day'].year == today_date.year if line['day'] else 0),
                    list,
                ),
        }
        return classified_data


    @api.depends('date')
    def compute_dates(self):
        for rec in self:
            rec.ptd = False
            rec.ytd = False
            if rec.date:
                rec.ptd = rec.date.replace(day=1)
                rec.ytd = rec.date.replace(day=1, month=1)

    @api.depends('room_charge_line_ids.date_total')
    def compute_room_charge_date_total(self):
        for rec in self:
            rec.room_charge_date_total = sum(rec.room_charge_line_ids.filtered(
                lambda l: l.charge_type not in ['municipality', 'vat']
            ).mapped('date_total') or [])
            rec.room_charge_tax_date_total = sum(rec.room_charge_line_ids.filtered(
                lambda l: l.charge_type in ['municipality', 'vat']
            ).mapped('date_total') or [])

    @api.depends('room_charge_line_ids.ptd_total')
    def compute_room_charge_ptd_total(self):
        for rec in self:
            rec.room_charge_ptd_total = sum(rec.room_charge_line_ids.filtered(
                lambda l: l.charge_type not in ['municipality', 'vat']
            ).mapped('ptd_total') or [])
            rec.room_charge_tax_ptd_total = sum(rec.room_charge_line_ids.filtered(
                lambda l: l.charge_type in ['municipality', 'vat']
            ).mapped('ptd_total') or [])

    @api.depends('room_charge_line_ids.ytd_total')
    def compute_room_charge_ytd_total(self):
        for rec in self:
            rec.room_charge_ytd_total = sum(rec.room_charge_line_ids.filtered(
                lambda l: l.charge_type not in ['municipality', 'vat']
            ).mapped('ytd_total') or [])
            rec.room_charge_tax_ytd_total = sum(rec.room_charge_line_ids.filtered(
                lambda l: l.charge_type in ['municipality', 'vat']
            ).mapped('ytd_total') or [])

    @api.depends('extra_charge_line_ids.date_total')
    def compute_extra_charge_date_total(self):
        for rec in self:
            rec.extra_charge_date_total = sum(rec.extra_charge_line_ids.filtered(
                lambda l: not l.tax_type
            ).mapped('date_total') or [])
            rec.extra_charge_tax_date_total = sum(rec.extra_charge_line_ids.filtered(
                lambda l: l.tax_type
            ).mapped('date_total') or [])

    @api.depends('extra_charge_line_ids.ptd_total')
    def compute_extra_charge_ptd_total(self):
        for rec in self:
            rec.extra_charge_ptd_total = sum(rec.extra_charge_line_ids.filtered(
                lambda l: not l.tax_type
            ).mapped('ptd_total') or [])
            rec.extra_charge_tax_ptd_total = sum(rec.extra_charge_line_ids.filtered(
                lambda l: l.tax_type
            ).mapped('ptd_total') or [])

    @api.depends('extra_charge_line_ids.ytd_total')
    def compute_extra_charge_ytd_total(self):
        for rec in self:
            rec.extra_charge_ytd_total = sum(rec.extra_charge_line_ids.filtered(
                lambda l: not l.tax_type
            ).mapped('ytd_total') or [])
            rec.extra_charge_tax_ytd_total = sum(rec.extra_charge_line_ids.filtered(
                lambda l: l.tax_type
            ).mapped('ytd_total') or [])

    @api.depends('room_charge_date_total', 'extra_charge_date_total')
    def compute_total_date_revenue_without_tax(self):
        for rec in self:
            rec.total_date_revenue_without_tax = rec.room_charge_date_total + rec.extra_charge_date_total

    @api.depends('room_charge_ptd_total', 'extra_charge_ptd_total')
    def compute_total_ptd_revenue_without_tax(self):
        for rec in self:
            rec.total_ptd_revenue_without_tax = rec.room_charge_ptd_total + rec.extra_charge_ptd_total

    @api.depends('room_charge_ytd_total', 'extra_charge_ytd_total')
    def compute_total_ytd_revenue_without_tax(self):
        for rec in self:
            rec.total_ytd_revenue_without_tax = rec.room_charge_ytd_total + rec.extra_charge_ytd_total

    @api.depends('room_charge_tax_date_total', 'extra_charge_tax_date_total')
    def compute_total_date_revenue_with_tax(self):
        for rec in self:
                                        # this contains room charge and extra  #this contains only room charge tax  #this contains only extra charge tax
            rec.total_date_revenue_with_tax = rec.total_date_revenue_without_tax + rec.room_charge_tax_date_total + rec.extra_charge_tax_date_total

    @api.depends('room_charge_tax_ptd_total', 'extra_charge_tax_ptd_total')
    def compute_total_ptd_revenue_with_tax(self):
        for rec in self:
            rec.total_ptd_revenue_with_tax = rec.total_ptd_revenue_without_tax + rec.room_charge_tax_ptd_total + rec.extra_charge_tax_ptd_total

    @api.depends('room_charge_tax_ytd_total', 'extra_charge_tax_ytd_total')
    def compute_total_ytd_revenue_with_tax(self):
        for rec in self:
            rec.total_ytd_revenue_with_tax = rec.total_ytd_revenue_without_tax + rec.room_charge_tax_ytd_total + rec.extra_charge_tax_ytd_total

    @api.depends('payment_line_ids.date_total')
    def compute_payment_date_total(self):
        for rec in self:
            rec.payment_date_total = sum(rec.payment_line_ids.mapped('date_total') or [])

    @api.depends('payment_line_ids.ptd_total')
    def compute_payment_ptd_total(self):
        for rec in self:
            rec.payment_ptd_total = sum(rec.payment_line_ids.mapped('ptd_total') or [])

    @api.depends('payment_line_ids.ytd_total')
    def compute_payment_ytd_total(self):
        for rec in self:
            rec.payment_ytd_total = sum(rec.payment_line_ids.mapped('ytd_total') or [])

    def button_search(self):
        self.create_room_charge_lines()
        self.create_extra_charge_lines()
        self.create_payment_lines()
        self.create_room_lines()
        self.generate_guest_ledger()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Manager Report'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hotel.manager.report',
            'res_id': self.id,
            'target': 'new'
        }
    def create_room_charge_lines(self):
        self.room_charge_line_ids = [(5, 0, 0)]
        folio_line_ids = self.env['booking.folio'].search([
            ('state', 'not in', ['draft', 'cancelled']),
            ('partner_id', '!=', False),
        ]).line_ids

        date_folio_line_ids = folio_line_ids.filtered(lambda l: self.date == l.day)

        ptd_folio_line_ids = folio_line_ids.filtered(lambda l: self.date.month == l.day.month and self.date.year == l.day.year)

        ytd_folio_line_ids = folio_line_ids.filtered(lambda l: self.date.year == l.day.year)

        room_charge_folios = date_folio_line_ids.filtered(lambda l: l.day == self.date and l.type == 'room_charge')
        ptd_room_charge_folios = ptd_folio_line_ids.filtered(lambda l: self.date >= l.day >= self.ptd and l.type == 'room_charge')
        ytd_room_charge_folios = ytd_folio_line_ids.filtered(lambda l: self.date >= l.day >= self.ytd and l.type == 'room_charge')

        total_room_charge = sum(room_charge_folios.filtered(lambda l: (not l.room_charge_type and l.particulars == 'Room Charge')).mapped('amount'))
        total_ptd_room_charge = sum(ptd_room_charge_folios.filtered(lambda l: (not l.room_charge_type and l.particulars == 'Room Charge')).mapped('amount'))
        total_ytd_room_charge = sum(ytd_room_charge_folios.filtered(lambda l: (not l.room_charge_type and l.particulars == 'Room Charge')).mapped('amount'))

        total_manual_room_charge = sum(room_charge_folios.filtered(lambda l: (l.room_charge_type == 'manual' or l.particulars == 'Manual Room Charge')).mapped('amount'))
        total_ptd_manual_room_charge = sum(ptd_room_charge_folios.filtered(lambda l: (l.room_charge_type == 'manual' or l.particulars == 'Manual Room Charge')).mapped('amount'))
        total_ytd_manual_room_charge = sum(ytd_room_charge_folios.filtered(lambda l: (l.room_charge_type == 'manual' or l.particulars == 'Manual Room Charge')).mapped('amount'))

        total_cancellation_room_charge = sum(room_charge_folios.filtered(lambda l: (l.room_charge_type == 'cancellation' or l.particulars == 'Cancellation Room Charge')).mapped('amount'))
        total_ptd_cancellation_room_charge = sum(ptd_room_charge_folios.filtered(lambda l: (l.room_charge_type == 'cancellation' or l.particulars == 'Cancellation Room Charge')).mapped('amount'))
        total_ytd_cancellation_room_charge = sum(ytd_room_charge_folios.filtered(lambda l: (l.room_charge_type == 'cancellation' or l.particulars == 'Cancellation Room Charge')).mapped('amount'))

        total_no_show_room_charge = sum(room_charge_folios.filtered(lambda l: (l.room_charge_type == 'no_show' or l.particulars == 'No Show Room Charge')).mapped('amount'))
        total_ptd_no_show_room_charge = sum(ptd_room_charge_folios.filtered(lambda l: (l.room_charge_type == 'no_show' or l.particulars == 'No Show Room Charge')).mapped('amount'))
        total_ytd_no_show_room_charge = sum(ytd_room_charge_folios.filtered(lambda l: (l.room_charge_type == 'no_show' or l.particulars == 'No Show Room Charge')).mapped('amount'))

        total_early_room_charge = sum(room_charge_folios.filtered(lambda l: (l.room_charge_type == 'early' or l.particulars == 'Early Check In Room Charge')).mapped('amount'))
        total_ptd_early_room_charge = sum(ptd_room_charge_folios.filtered(lambda l: (l.room_charge_type == 'early' or l.particulars == 'Early Check In Room Charge')).mapped('amount'))
        total_ytd_early_room_charge = sum(ytd_room_charge_folios.filtered(lambda l: (l.room_charge_type == 'early' or l.particulars == 'Early Check In Room Charge')).mapped('amount'))

        total_late_room_charge = sum(room_charge_folios.filtered(lambda l: (l.room_charge_type == 'late' or l.particulars == 'Late Check Out Room Charge')).mapped('amount'))
        total_ptd_late_room_charge = sum(ptd_room_charge_folios.filtered(lambda l: (l.room_charge_type == 'late' or l.particulars == 'Late Check Out Room Charge')).mapped('amount'))
        total_ytd_late_room_charge = sum(ytd_room_charge_folios.filtered(lambda l: (l.room_charge_type == 'late' or l.particulars == 'Late Check Out Room Charge')).mapped('amount'))
        # room charge taxes
        room_charge_tax_folios = date_folio_line_ids.filtered(lambda l: l.day == self.date and l.type == 'tax')
        ptd_room_charge_tax_folios = ptd_folio_line_ids.filtered(lambda l: self.date >= l.day >= self.ptd and l.type == 'tax')
        ytd_room_charge_tax_folios = ytd_folio_line_ids.filtered(lambda l: self.date >= l.day >= self.ytd and l.type == 'tax')

        total_date_room_charge_municipality = sum(room_charge_tax_folios.filtered(lambda l: l.tax_type == 'municipality' and not l.is_service_tax).mapped('amount'))
        total_ptd_room_charge_municipality = sum(ptd_room_charge_tax_folios.filtered(lambda l: l.tax_type == 'municipality' and not l.is_service_tax).mapped('amount'))
        total_ytd_room_charge_municipality = sum(ytd_room_charge_tax_folios.filtered(lambda l: l.tax_type == 'municipality' and not l.is_service_tax).mapped('amount'))

        total_date_room_charge_vat = sum(room_charge_tax_folios.filtered(lambda l: l.tax_type == 'vat' and not l.is_service_tax).mapped('amount'))
        total_ptd_room_charge_vat = sum(ptd_room_charge_tax_folios.filtered(lambda l: l.tax_type == 'vat' and not l.is_service_tax).mapped('amount'))
        total_ytd_room_charge_vat = sum(ytd_room_charge_tax_folios.filtered(lambda l: l.tax_type == 'vat' and not l.is_service_tax).mapped('amount'))


        # create lines
        self.room_charge_line_ids = [
            (0, 0, {
                'charge_type': 'room_charge',
                'date_total': total_room_charge,
                'ptd_total': total_ptd_room_charge,
                'ytd_total': total_ytd_room_charge,
            }), (0, 0, {
                'charge_type': 'manual',
                'date_total': total_manual_room_charge,
                'ptd_total': total_ptd_manual_room_charge,
                'ytd_total': total_ytd_manual_room_charge,
            }), (0, 0, {
                'charge_type': 'cancellation',
                'date_total': total_cancellation_room_charge,
                'ptd_total': total_ptd_cancellation_room_charge,
                'ytd_total': total_ytd_cancellation_room_charge,
            }), (0, 0, {
                'charge_type': 'no_show',
                'date_total': total_no_show_room_charge,
                'ptd_total': total_ptd_no_show_room_charge,
                'ytd_total': total_ytd_no_show_room_charge,
            }), (0, 0, {
                'charge_type': 'early',
                'date_total': total_early_room_charge,
                'ptd_total': total_ptd_early_room_charge,
                'ytd_total': total_ytd_early_room_charge,
            }), (0, 0, {
                'charge_type': 'late',
                'date_total': total_late_room_charge,
                'ptd_total': total_ptd_late_room_charge,
                'ytd_total': total_ytd_late_room_charge,
            }),(0, 0, {
                'charge_type': 'municipality',
                'date_total': total_date_room_charge_municipality,
                'ptd_total': total_ptd_room_charge_municipality,
                'ytd_total': total_ytd_room_charge_municipality,
            }),(0, 0, {
                'charge_type': 'vat',
                'date_total': total_date_room_charge_vat,
                'ptd_total': total_ptd_room_charge_vat,
                'ytd_total': total_ytd_room_charge_vat,
            }),
        ]

    def create_extra_charge_lines(self):
        particulars = self.env['ir.config_parameter'].sudo().get_param('hotel_booking.particulars')
        self.extra_charge_line_ids = [(5, 0, 0)]
        folio_line_ids = self.env['booking.folio'].search([
            ('state', 'not in', ['draft', 'cancelled']),
            ('partner_id', '!=', False),
        ]).line_ids

        extra_charge_folios = folio_line_ids.filtered(lambda l: l.type in ['food', 'rent', 'beverage', 'laundry'])
        date_extra_charge_folios = extra_charge_folios.filtered(lambda l: l.day == self.date)
        ptd_extra_charge_folios = extra_charge_folios.filtered(lambda l: self.date >= l.day >= self.ptd)
        ytd_extra_charge_folios = extra_charge_folios.filtered(lambda l: self.date >= l.day >= self.ytd)
        services = list(set(extra_charge_folios.mapped('particulars')))
        for service in services:
            total_date_extra_charge = sum(date_extra_charge_folios.filtered(lambda l: l.particulars == service).mapped('amount'))
            total_ptd_extra_charge = sum(ptd_extra_charge_folios.filtered(lambda l: l.particulars == service).mapped('amount'))
            total_ytd_extra_charge = sum(ytd_extra_charge_folios.filtered(lambda l: l.particulars == service).mapped('amount'))
            self.extra_charge_line_ids = [
                (0, 0, {
                    'name': service,
                    'date_total': total_date_extra_charge,
                    'ptd_total': total_ptd_extra_charge,
                    'ytd_total': total_ytd_extra_charge,
                }),]
        # taxes
        extra_charge_municipality_folios = folio_line_ids.filtered(lambda l: l.tax_type == 'municipality' and l.is_service_tax)
        total_date_extra_charge_municipality = sum(extra_charge_municipality_folios.filtered(lambda l: l.day == self.date).mapped('amount'))
        total_ptd_extra_charge_municipality = sum(extra_charge_municipality_folios.filtered(lambda l: self.date >= l.day >= self.ptd).mapped('amount'))
        total_ytd_extra_charge_municipality = sum(extra_charge_municipality_folios.filtered(lambda l: self.date >= l.day >= self.ytd).mapped('amount'))

        extra_charge_vat_folios = folio_line_ids.filtered(lambda l: l.tax_type == 'vat' and l.is_service_tax)
        total_date_extra_charge_vat = sum(extra_charge_vat_folios.filtered(lambda l: l.day == self.date).mapped('amount'))
        total_ptd_extra_charge_vat = sum(extra_charge_vat_folios.filtered(lambda l: self.date >= l.day >= self.ptd).mapped('amount'))
        total_ytd_extra_charge_vat = sum(extra_charge_vat_folios.filtered(lambda l: self.date >= l.day >= self.ytd).mapped('amount'))

        self.extra_charge_line_ids = [
            (0, 0, {
                'name': particulars,
                'tax_type': 'municipality',
                'date_total': total_date_extra_charge_municipality,
                'ptd_total': total_ptd_extra_charge_municipality,
                'ytd_total': total_ytd_extra_charge_municipality,
            }),(0, 0, {
                'name': 'VAT',
                'tax_type': 'vat',
                'date_total': total_date_extra_charge_vat,
                'ptd_total': total_ptd_extra_charge_vat,
                'ytd_total': total_ytd_extra_charge_vat,
            }),
        ]

    def create_payment_lines(self):
        self.payment_line_ids = [(5, 0, 0)]
        payment_ids = self.env['account.payment'].search([
            ('state', '=', 'posted'),
        ]).filtered(lambda p: p.audit_date.year == self.date.year)
        date_payment_ids = payment_ids.filtered(lambda p: p.audit_date == self.date)
        ptd_payment_ids = payment_ids.filtered(lambda p: self.date >= p.audit_date >= self.ptd)
        ytd_payment_ids = payment_ids.filtered(lambda p: self.date >= p.audit_date >= self.ytd)
        journals = list(set(payment_ids.mapped('journal_id')))
        for journal in journals:
            total_date_payment = sum(date_payment_ids.filtered(lambda p: p.journal_id.id == journal.id).mapped('amount'))
            total_ptd_payment = sum(ptd_payment_ids.filtered(lambda p: p.journal_id.id == journal.id).mapped('amount'))
            total_ytd_payment = sum(ytd_payment_ids.filtered(lambda p: p.journal_id.id == journal.id).mapped('amount'))
            self.payment_line_ids = [
                (0, 0, {
                    'journal_id': journal.id,
                    'date_total': abs(total_date_payment),
                    'ptd_total': abs(total_ptd_payment),
                    'ytd_total': abs(total_ytd_payment),
                }), ]

    def create_room_lines(self):
        self.room_line_ids = [(5, 0, 0)]
        rooms = self.env['hotel.room'].search([('company_id', '=', self.company_id.id)])
        ptd_days = (self.date - self.ptd).days + 1
        ytd_days = (self.date - self.ytd).days + 1
        self.room_line_ids = [
            (0, 0, {
                'name': "Total Room",
                'date_total': len(rooms),
                'ptd_total': len(rooms) * ptd_days,
                'ytd_total': len(rooms) * ytd_days,
            }), ]
        # Out of Order Rooms
        out_of_order_rooms_query = """
            SELECT DATETIME::DATE AS DAY,NOTES,ROOM_ID
            FROM AUDIT_TRAILS
            WHERE OPERATION = 'update_room_stay_state'
            AND NOTES ilike '%%To Stay Status: Out of Order%%'
            AND DATETIME::DATE BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::DATE
            """
        self.env.cr.execute(out_of_order_rooms_query,{
            'today_date': self.date.strftime('%Y-%m-%d'),
            'company_id': self.env.company.id,
        })
        out_of_order_rooms_data = self.env.cr.dictfetchall()
        out_of_order_rooms = T.pipe(
            out_of_order_rooms_data,
            lambda lines: self._classify_data(lines, self.date),
            TC.valmap(TC.count),

        )
        self.room_line_ids = [
            (0, 0, {
                'name': "Block Room",
                'date_total': out_of_order_rooms.get('today', 0),
                'ptd_total': out_of_order_rooms.get('month', 0),
                'ytd_total': out_of_order_rooms.get('year', 0),
            }), ]
        folios = self.env['booking.folio'].search([
            ('state', 'not in', ['cancelled']), ('partner_id', '!=', False),
            ('room_id', '!=', False)
        ])
        '''
        There are 3 cases of overlapping to consider for ptd:
        s1   s2   e1   e2
        (    [----)----]
        s2   s1   e2   e1
        [----(----]    )
        s1   s2   e2   e1
        (    [----]    )
        '''
        date_folios = folios.filtered(lambda f: f.new_check_out > self.date >= f.new_check_in)
        ptd_folios = self.env['booking.folio'].search([
            ('id', 'in', folios.ids), '|', '|',
                '&', ('check_in_date', '<=', self.ptd), ('check_out_date', '>', self.ptd),
                '&', ('check_in_date', '<=', self.date), ('check_out_date', '>', self.date),
                '&', ('check_in_date', '<=', self.ptd), ('check_out_date', '>', self.date),

        ])
        ytd_folios = folios.filtered(lambda f: f.new_check_out > self.ytd and self.ytd <= f.new_check_in)
        total_booked_rooms_query = """
        SELECT BFL.DAY AS DAY,	COUNT(BFL.*) AS BOOKED
        FROM BOOKING_FOLIO_LINE AS BFL
            INNER JOIN BOOKING_FOLIO AS BF ON BF.ID = BFL.FOLIO_ID
            AND BF.STATE != 'cancelled'
            AND BF.COMPANY_ID IS NOT NULL
            AND BF.ROOM_TYPE_ID IS NOT NULL
            AND BF.COMPANY_ID =  %(company_id)s
            AND BFL.PARTICULARS = 'Room Charge'
            AND BFL.DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
        GROUP BY BFL.DAY
        """
        self.env.cr.execute(total_booked_rooms_query, {
            'today_date': self.date.strftime('%Y-%m-%d'),
            'company_id': self.env.company.id,
        })
        total_booked_rooms_data = self.env.cr.dictfetchall()
        total_booked_rooms = T.pipe(
            total_booked_rooms_data,
            lambda lines: self._classify_data(lines, self.date),
            TC.valmap(TC.map(TC.get('booked'))),
            TC.valmap(sum),
        )
        total_day_use_booked_rooms_query = """
        SELECT BFL.DAY AS DAY,	COUNT(BFL.*) AS BOOKED
        FROM BOOKING_FOLIO_LINE AS BFL
            INNER JOIN BOOKING_FOLIO AS BF ON BF.ID = BFL.FOLIO_ID
            AND BF.STATE != 'cancelled'
            AND BF.COMPANY_ID IS NOT NULL
            AND BF.ROOM_TYPE_ID IS NOT NULL
            AND BF.COMPANY_ID =  %(company_id)s
            AND BFL.PARTICULARS = 'Room Charge'
            AND BF.DAY_USE = TRUE
            AND BFL.DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
        GROUP BY BFL.DAY
        """
        self.env.cr.execute(total_day_use_booked_rooms_query, {
            'today_date': self.date.strftime('%Y-%m-%d'),
            'company_id': self.env.company.id,
        })
        total_day_use_booked_rooms_data = self.env.cr.dictfetchall()
        total_day_use_booked_rooms = T.pipe(
            total_day_use_booked_rooms_data,
            lambda lines: self._classify_data(lines, self.date),
            TC.valmap(TC.map(TC.get('booked'))),
            TC.valmap(sum),
        )
        # ===============================================
        room_charge_revenue_query = """
        WITH HOTEL_ROOM_CHARGE AS (
            SELECT NAME FROM HOTEL_ROOM_CHARGE
            UNION
            SELECT 'Room Charge' AS NAME
        )
        SELECT
        BS.NAME AS DESCRIPTION,
        SUM(BF.NUMBER_OF_GUESTS) AS COVER,
        SUM(BFL.AMOUNT) AS REVENUE,
        '#' AS BUDGET,
        BFL.DAY,
        COALESCE(HB.DAY_USE,FALSE) AS DAY_USE,
        COALESCE(HB.HOUSE_USE,FALSE) AS HOUSE_USE,
        COALESCE(HB.COMPLIMENTARY_ROOM,FALSE) AS COMPLIMENTARY
        FROM HOTEL_BOOKING AS HB
        INNER JOIN BOOKING_FOLIO AS BF ON BF.BOOKING_ID = HB.ID AND HB.COMPANY_ID = %(company_id)s
        INNER JOIN BOOKING_FOLIO_LINE AS BFL ON BFL.FOLIO_ID = BF.ID
            AND HB.STATE != 'cancelled'
            AND BFL.PARTICULARS IN  (SELECT NAME FROM HOTEL_ROOM_CHARGE)
            AND BFL.DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
        RIGHT JOIN BOOKING_SOURCE AS BS ON BS.NAME = HB.BOOKING_SOURCE
        GROUP BY  (BS.NAME, BFL.DAY,HB.DAY_USE,HB.HOUSE_USE,HB.COMPLIMENTARY_ROOM)
        ORDER BY BS.NAME
        """
        self.env.cr.execute(
            room_charge_revenue_query,
            {
                'today_date': self.date.strftime('%Y-%m-%d'),
                'company_id': self.env.company.id,
            },
        )
        room_charge_revenue_data = self.env.cr.dictfetchall()
        number_of_guest = T.pipe(
            room_charge_revenue_data,
            TC.filter(lambda line: not line['day_use']),
            list,
            lambda lines: self._classify_data(lines, self.date),
            TC.valmap(lambda lines : sum(TC.pluck('cover',lines))),
            )
        self.room_line_ids = [
            (0, 0, {
                'name': "No of Guest (Adult/Child)",
                'date_total': number_of_guest.get('today', 0),
                'ptd_total': number_of_guest.get('month', 0),
                'ytd_total': number_of_guest.get('year', 0),
            }), ]
        self.room_line_ids = [
            (0, 0, {
                'name': "Total Available Room nights",
                'date_total': len(rooms) - total_booked_rooms.get('today', 0) + total_day_use_booked_rooms.get('today', 0),
                'ptd_total': len(rooms) * ptd_days - total_booked_rooms.get('month', 0) + total_day_use_booked_rooms.get('month', 0),
                'ytd_total': len(rooms) * ytd_days - total_booked_rooms.get('year', 0) + total_day_use_booked_rooms.get('year', 0),
            }), ]
        self.room_line_ids = [
            (0, 0, {
                'name': "Sold Room",
                'date_total': total_booked_rooms.get('today', 0),
                'ptd_total': total_booked_rooms.get('month', 0),
                'ytd_total': total_booked_rooms.get('year', 0),
            }), ]
        self.room_line_ids = [
            (0, 0, {
                'name': "Day Use Room",
                'date_total': total_day_use_booked_rooms.get('today', 0),
                'ptd_total': total_day_use_booked_rooms.get('month', 0),
                'ytd_total': total_day_use_booked_rooms.get('year', 0),
            }), ]
        # ======================================================
        complimentary_rooms = """
        WITH HOTEL_ROOM_CHARGE AS (
            SELECT NAME FROM HOTEL_ROOM_CHARGE
            UNION
            SELECT 'Room Charge' AS NAME
        )
        SELECT
        BFL.DAY,
        COUNT(*) AS TOTAL
        FROM HOTEL_BOOKING AS HB
        INNER JOIN BOOKING_FOLIO AS BF ON BF.BOOKING_ID = HB.ID AND HB.COMPANY_ID = %(company_id)s
        INNER JOIN BOOKING_FOLIO_LINE AS BFL ON BFL.FOLIO_ID = BF.ID
            AND HB.STATE != 'cancelled'
            AND  HB.COMPLIMENTARY_ROOM
            AND BFL.PARTICULARS IN  (SELECT NAME FROM HOTEL_ROOM_CHARGE)
            AND BFL.DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
        GROUP BY  (BFL.DAY,HB.HOUSE_USE,HB.COMPLIMENTARY_ROOM)
        """
        self.env.cr.execute(complimentary_rooms, {
            'today_date': self.date.strftime('%Y-%m-%d'),
            'company_id': self.env.company.id,
        })
        complimentary_rooms_data = self.env.cr.dictfetchall()
        structured_complimentary = T.pipe(
            complimentary_rooms_data,
            lambda lines: self._classify_data(lines, self.date),
            TC.valmap(lambda lines : sum(TC.pluck('total',lines))),
        )
        # ==============================================================
        draft_confirm_cancel_folio_query = """
        SELECT BFL.DAY AS DAY,COUNT(BFL.*) AS TOTAL, BF.STATE
        FROM BOOKING_FOLIO_LINE AS BFL
            INNER JOIN BOOKING_FOLIO AS BF ON BF.ID = BFL.FOLIO_ID
            AND BF.COMPANY_ID IS NOT NULL
            AND BF.ROOM_TYPE_ID IS NOT NULL
            AND BF.COMPANY_ID =  %(company_id)s
            AND BFL.PARTICULARS = 'Room Charge'
            AND BFL.DAY BETWEEN SYMMETRIC %(today_date)s AND DATE_TRUNC('year', TO_DATE(%(today_date)s, 'YYYY-MM-DD'))::date
        GROUP BY BFL.DAY, BF.STATE
        """
        self.env.cr.execute(draft_confirm_cancel_folio_query, {
            'today_date': self.date.strftime('%Y-%m-%d'),
            'company_id': self.env.company.id,
        })
        draft_confirm_cancel_folio_data = self.env.cr.dictfetchall()
        structured_draft_confirm_cancel_folio = T.pipe(
        draft_confirm_cancel_folio_data,
        TC.groupby('state'),
        TC.valmap(
            TC.compose_left(
                lambda lines: self._classify_data(lines,self.date),
                TC.valmap(TC.pluck('total')),
                TC.valmap(sum),
            )))

        self.room_line_ids = [
            (0, 0, {
                'name': "Complimentary Room",
                'date_total': structured_complimentary.get('today', 0),
                'ptd_total': structured_complimentary.get('month', 0),
                'ytd_total': structured_complimentary.get('year', 0),
                'date_total_str': f"{structured_complimentary.get('today', 0),}",
                'ptd_total_str': f"{structured_complimentary.get('month', 0),}",
                'ytd_total_str': f"{structured_complimentary.get('year', 0),}",
            }), ]
        self.room_line_ids = [
            (0, 0, {
                'hide_from_report': True,
                'name': "Complimentary Day Use",
                'date_total': structured_complimentary.get('today', 0),
                'ptd_total': structured_complimentary.get('month', 0),
                'ytd_total': structured_complimentary.get('year', 0),
            }), ]
        self.room_line_ids = [
            (0, 0, {
                'name': "No Show Rooms",
                'date_total': structured_draft_confirm_cancel_folio.get('cancelled',{}).get('today'),
                'ptd_total': structured_draft_confirm_cancel_folio.get('cancelled',{}).get('month'),
                'ytd_total': structured_draft_confirm_cancel_folio.get('cancelled',{}).get('year'),
            }), ]
        self.room_line_ids = [
            (0, 0, {
                'name': "Average Guest Per Room",
                'date_total':self.divide(number_of_guest.get('today', 0) , total_booked_rooms.get('today', 0)),
                'ptd_total':self.divide(number_of_guest.get('month', 0) , total_booked_rooms.get('month', 0)),
                'ytd_total':self.divide(number_of_guest.get('year', 0) , total_booked_rooms.get('year', 0)),
            }), ]
        self.room_line_ids = [
            (0, 0, {
                'name': "No of Reservations (Confirmed)",
                'date_total': structured_draft_confirm_cancel_folio.get('confirmed',{}).get('today'),
                'ptd_total':  structured_draft_confirm_cancel_folio.get('confirmed',{}).get('month'),
                'ytd_total':  structured_draft_confirm_cancel_folio.get('confirmed',{}).get('year'),
            }), ]
        self.room_line_ids = [
            (0, 0, {
                'name': "No of Reservations (Unconfirmed)",
                'date_total': structured_draft_confirm_cancel_folio.get('draft',{}).get('today',0),
                'ptd_total': structured_draft_confirm_cancel_folio.get('draft',{}).get('month',0),
                'ytd_total': structured_draft_confirm_cancel_folio.get('draft',{}).get('year',0),
            }), ]
        if len(rooms):
            # self.room_line_ids = [(0, 0, {'name': "Statistics", }), ]
            date_rate = len(date_folios) / len(rooms)
            ptd_rate = len(ptd_folios) / (len(rooms) * (ptd_days or 1))
            ytd_rate = len(ytd_folios) / (len(rooms) * (ytd_days or 1))
            self.room_line_ids = [
                (0, 0, {
                    'name': "Occupancy Rate(%)",
                    'date_total': total_booked_rooms.get('today', 0) /len(rooms) ,
                    'ptd_total': total_booked_rooms.get('month', 0)/ (len(rooms) * ptd_days),
                    'ytd_total': total_booked_rooms.get('year', 0)/ (len(rooms) * ytd_days),
                }), ]
            if len(date_folios) and len(ptd_folios) and len(ytd_folios):
                total_date_room_charge = self.room_charge_line_ids.filtered(lambda l: l.charge_type == 'room_charge').date_total
                total_ptd_room_charge = self.room_charge_line_ids.filtered(lambda l: l.charge_type == 'room_charge').ptd_total
                total_ytd_room_charge = self.room_charge_line_ids.filtered(lambda l: l.charge_type == 'room_charge').ytd_total
                self.room_line_ids = [
                    (0, 0, {
                        'name': "Average Daily Rate(ADR)",
                        'date_total': total_date_room_charge / len(date_folios),
                        'ptd_total': total_ptd_room_charge / len(ptd_folios),
                        'ytd_total': total_ytd_room_charge / len(ytd_folios),
                    }), ]
                self.room_line_ids = [
                    (0, 0, {
                        'name': "Revenue Per Available Room",
                        'date_total': (total_date_room_charge / len(date_folios)) * date_rate,
                        'ptd_total': total_ptd_room_charge / len(ptd_folios) * ptd_rate,
                        'ytd_total': total_ytd_room_charge / len(ytd_folios) * ytd_rate,
                    }), ]

    def generate_guest_ledger(self):
        wizard = self.env['guest.ledger'].create({'date': self.date})
        wizard.button_search()
        self.total_virtual = wizard.total_virtual
        self.total_actual = wizard.total_actual
        self.total_balance = wizard.total_balance

    def print_pdf(self):
        return self.env.ref('hotel_booking_folio.action_hotel_manager_report').report_action(self)


class RoomChargeManagerReport(models.TransientModel):
    _name = 'room.charge.manager.report'
    _description = 'Room Charge Manager Report'

    wizard_id = fields.Many2one('hotel.manager.report')
    charge_type = fields.Selection([
        ('room_charge', 'Room Charge'),
        ('manual', 'Manual'),
        ('cancellation', 'Cancellation'),
        ('no_show', 'No Show'),
        ('early', 'Early'),
        ('late', 'Late'),
        ('municipality', 'Municipality'),
        ('vat', 'VAT'),
    ], required=True)
    date_total = fields.Float(digits=(4,5))
    ptd_total = fields.Float(digits=(4,5))
    ytd_total = fields.Float(digits=(4,5))


class ExtraChargeManagerReport(models.TransientModel):
    _name = 'extra.charge.manager.report'
    _description = 'Extra Charge Manager Report'

    wizard_id = fields.Many2one('hotel.manager.report')
    name = fields.Char()
    tax_type = fields.Selection([
        ('municipality', 'Municipality'),
        ('vat', 'VAT'),
    ])
    date_total = fields.Float()
    ptd_total = fields.Float()
    ytd_total = fields.Float()


class PaymentManagerReport(models.TransientModel):
    _name = 'payment.manager.report'
    _description = 'Payment Manager Report'

    wizard_id = fields.Many2one('hotel.manager.report')
    journal_id = fields.Many2one('account.journal')
    date_total = fields.Float()
    ptd_total = fields.Float()
    ytd_total = fields.Float()


class RoomManagerReport(models.TransientModel):
    _name = 'room.manager.report'
    _description = 'Room Manager Report'

    wizard_id = fields.Many2one('hotel.manager.report')
    name = fields.Char()
    date_total = fields.Float(digits=(4,5))
    ptd_total = fields.Float(digits=(4,5))
    ytd_total = fields.Float(digits=(4,5))
    date_total_str = fields.Char()
    ptd_total_str = fields.Char()
    ytd_total_str = fields.Char()
    hide_from_report = fields.Boolean()
