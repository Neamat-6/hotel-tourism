import datetime
import re
import json

from odoo import api, models, fields, http, SUPERUSER_ID
from odoo.http import request, content_disposition
from dateutil.relativedelta import relativedelta


class RoomAvailabilityDashboard(models.TransientModel):
    _name = 'room.availability.dashboard'
    _description = 'Room Availability Dashboard'

    start_date = fields.Date()
    end_date = fields.Date()
    hotel_id = fields.Many2one('hotel.hotel')

    @api.model
    def create_wizard(self, start_date, end_date):
        if start_date != 'null' and end_date != 'null':
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        elif start_date == 'null' and end_date != 'null':
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            start_date = end_date
        elif start_date != 'null' and end_date == 'null':
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = start_date
        else:
            start_date = self.env.company.audit_date
            end_date = start_date + relativedelta(days=3)

        wizard = self.env['room.availability.dashboard'].sudo().create({
            'hotel_id': self.env.company.related_hotel_id.id,
            'start_date': start_date,
            'end_date': end_date,
        })
        return wizard.id

    @api.model
    def create_wizard_with_attachment(self, start_date, end_date):
        if start_date != 'null' and end_date != 'null':
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        elif start_date == 'null' and end_date != 'null':
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            start_date = end_date
        elif start_date != 'null' and end_date == 'null':
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = start_date
        else:
            start_date = self.env.company.audit_date
            end_date = start_date + relativedelta(days=3)

        wizard = self.env['room.availability.dashboard'].sudo().create({
            'hotel_id': self.env.company.related_hotel_id.id,
            'start_date': start_date,
            'end_date': end_date,
        })
        _context = self.env.context
        context = {
            "lang": _context.get("lang", False),
            "tz": _context.get("tz", False),
            "uid": _context.get("uid", False),
            "allowed_company_ids": _context.get("allowed_company_ids", False),
            "active_model": "room.availability.dashboard",
            "active_id": wizard.id,
            "active_ids": wizard.ids,
            "discard_logo_check": True,
            "landscape": True
        }
        data = {
            "context": json.dumps(context),
            "ids": [],
            "model": 'ir.ui.menu',
            "form": {
                "id": wizard.id,
                "start_date": wizard.start_date,
                "end_date": wizard.end_date,
                "used_context": {
                    "start_date": wizard.start_date,
                    "end_date": wizard.end_date,
                    "lang": _context.get("lang", False)
                },
            },
            "report_type": "pdf"
        }
        content, content_type = self.env.ref('room_availability_dashboard.action_room_availability_report').with_context(landscape=True)._render(res_ids=wizard.ids, data=data)
        attachment = self.env['ir.attachment'].create({
            'name': "RoomAvailabilityReport.pdf",
            'type': 'binary',
            'raw': content,
            'res_model': 'room.availability.dashboard',
            'res_id': wizard.id
        })

        return [wizard.id, attachment.id]
