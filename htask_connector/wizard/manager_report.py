# -*- coding: utf-8 -*-
# from dateutil import parser
from odoo import models, fields, api, _
import pytz
# from dateutil.tz import tzlocal
from datetime import timedelta, datetime
# from itertools import groupby
# from operator import itemgetter
# from odoo.exceptions import UserError
# import re
# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools import date_utils


class ManagerReport(models.TransientModel):
    _name = "manager.report"

    date = fields.Date(required=True, default=fields.Date.today())

    def generate_manager_report(self):

        user_time_zone = self.env.user.tz
        user_tz = pytz.timezone(user_time_zone)
        utc_tz = pytz.timezone('UTC')
        
        date_time = datetime(self.date.year, self.date.month, self.date.day)
        date_timezone = date_time.astimezone(utc_tz)

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date': fields.Date.to_string(date_timezone),
            },
        }
        return self.env.ref('htask_connector.daily_revenues_manager_report').report_action([], data=data)


class ReportDailyRevenues(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.htask_connector.manager_report_daily_revenues'

    @api.model
    def _get_report_values(self, docids, data=None):

        date_dt = data['form']['date']
        date_time = datetime.strptime(date_dt, '%Y-%m-%d').date()
        MoveLine = self.env['account.move.line']
        
        year_start = date_utils.start_of(date_time, 'year')
        month_start = date_utils.start_of(date_time, 'month')

        self.env.cr.execute("""
            SELECT aml.id, aml.date, aml.balance, acc.name as acc
            FROM account_move_line aml, account_account acc, account_move mv
            WHERE aml.account_id = acc.id
            AND aml.move_id = mv.id
            AND mv.htask_id_external is not null
            AND aml.date >= %s AND aml.date < %s
            ORDER BY aml.date
        """, (year_start, date_time))

        year_move_lines = self.env.cr.dictfetchall()        
        
        totals_yr = {}
        totals_mt = {}
        totals_dt = {}

        month_move_lines = []
        day_move_lines = []

        for y_mv_line in year_move_lines:
            acc = y_mv_line['acc']
            if acc not in totals_yr:
                totals_yr[acc] = 0.0
            if y_mv_line['date'] >= month_start and y_mv_line['date'] < date_time:
                month_move_lines.append(y_mv_line)
            totals_yr[acc] += y_mv_line['balance']

        for m_mv_line in month_move_lines:
            acc = m_mv_line['acc']
            if acc not in totals_mt:
                totals_mt[acc] = 0.0
            if m_mv_line['date'] == date_time:
                day_move_lines.append(m_mv_line)
            totals_mt[acc] += m_mv_line['balance']

        for d_mv_line in day_move_lines:
            acc = d_mv_line['acc']
            if acc not in totals_dt:
                totals_dt[acc] = 0.0
            totals_dt[acc] += d_mv_line['balance']


        account_ids = self.env['htask.account.configuration'].search([])
        
        data = []

        for acc in account_ids:
            today = round(totals_dt.get(acc.htask_account, 0.0), 2)
            ptd = round(totals_mt.get(acc.htask_account, 0.0), 2)
            ytd = round(totals_yr.get(acc.htask_account, 0.0), 2)
            data.append({
                'type': acc.htask_type_id.name, 
                'account': acc.htask_account, 
                'today': today * -1 if today != 0.0 else 0.0, 
                'ptd': ptd * -1 if ptd != 0.0 else 0.0, 
                'ytd': ytd * -1 if ytd != 0.0 else 0.0, 
            })


        categs = ['Room Revenue', 'Extra Charges', 'Discount', 'Adjustments', 'Taxes']
        
        return {
            'categs': categs,
            'data': data,
            'date_time': datetime.strptime(date_dt, '%Y-%m-%d'),
        }
