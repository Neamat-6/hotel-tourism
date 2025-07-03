from odoo import models, fields, api
from hijri_converter import Gregorian

from odoo.exceptions import ValidationError


class SeasonDuration(models.Model):
    _name = 'season.duration'
    _description = 'Season Duration'

    name = fields.Char(string='Season Name', required=True)
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    hijri_date_from = fields.Char(string='Start Date (Hijri)', compute='_compute_hijri_dates', store=True)
    hijri_date_to = fields.Char(string='End Date (Hijri)', compute='_compute_hijri_dates', store=True)

    @api.depends('date_from', 'date_to')
    def _compute_hijri_dates(self):
        for record in self:
            if record.date_from:
                gregorian_from = Gregorian.fromisoformat(record.date_from.isoformat())
                hijri_from = gregorian_from.to_hijri()
                record.hijri_date_from = hijri_from.isoformat()
            else:
                record.hijri_date_from = False

            if record.date_to:
                gregorian_to = Gregorian.fromisoformat(record.date_to.isoformat())
                hijri_to = gregorian_to.to_hijri()
                record.hijri_date_to = hijri_to.isoformat()
            else:
                record.hijri_date_to = False

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from > record.date_to:
                raise ValidationError("The start date cannot be after the end date.")
            overlapping_seasons = self.search([('id', '!=', record.id), ('date_from', '<=', record.date_to), ('date_to', '>=', record.date_from)])
            if overlapping_seasons:
                raise ValidationError("The season duration overlaps with another season.")
