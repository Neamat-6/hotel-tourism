# -*- coding: utf-8 -*-
# from dateutil import parser
from odoo import models, fields, api, _
# import pytz
# from dateutil.tz import tzlocal
from datetime import timedelta, datetime
# from itertools import groupby
# from operator import itemgetter
from odoo.exceptions import UserError, ValidationError
# import re
import time

# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
# from odoo.tools import date_utils


class HtaskSyncRevenues(models.TransientModel):
    _name = "htask.sync.revenues"

    start_date = fields.Datetime(required=True)
    end_date = fields.Datetime(required=True)

    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def sync_revenues(self):
        Account = self.env['account.move']

        if self.start_date > self.end_date:
            raise ValidationError(_("Start Date must be less or equal to end date"))

        delta = self.end_date - self.start_date

        if delta.days <= 88:  # limit ok
            date_start = self.start_date.strftime("%Y-%m-%d")  # to_string(self.start_date)
            date_end = self.end_date.strftime("%Y-%m-%d")  # .to_string(self.end_date)

            Account.button_sync_revenues(date_start, date_end)

        else:  # loop every 88 days:
            is_end = False
            start = self.start_date
            while not is_end:
                end = start + timedelta(days=88)
                if end > self.end_date:
                    end = self.end_date
                    is_end = True
                time.sleep(5)
                Account.button_sync_revenues(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                start = end
