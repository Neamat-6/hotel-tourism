from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class FolioBed(models.Model):
    _name = 'booking.folio.bed'
    _description = 'Folio Bed'

    folio_id = fields.Many2one('booking.folio', ondelete='cascade', string='Folio')
    partner_id = fields.Many2one('res.partner', string='Guest')
    bed_type_id = fields.Many2one('hotel.bed.type')
    today_is_checkin = fields.Boolean(compute='compute_today_is_checkin')
    today_is_checkout = fields.Boolean(compute='compute_today_is_checkout')
    checked_in_date = fields.Datetime()
    checked_out_date = fields.Datetime()
    state = fields.Selection([
        ('draft', 'Draft'), ('checked_in', 'Checked In'), ('checked_out', 'Checked Out'),
    ], default='draft', required=True)

    def button_check_in(self):
        if not self.partner_id:
            raise ValidationError("please select guest!")
        folio = self.folio_id

        if folio.available_beds == folio.total_beds:
            folio.partner_id = self.partner_id.id
            folio.button_check_in(True, self.partner_id)
        else:
            pass
            # folio.booking_id.send_by_whatsapp_direct('check_in', partner=self.partner_id)

        folio.available_beds -= 1
        if not folio.available_beds:
            folio.state = 'checked_in'
        self.state = 'checked_in'
        self.checked_in_date = fields.Datetime.now()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Folio'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.folio',
            'res_id': folio.id,
            'target': 'new'
        }

    def button_check_out(self):
        folio = self.folio_id
        # folio.booking_id.send_by_whatsapp_direct('check_out', partner=self.partner_id)

        all_beds = folio.bed_ids.filtered(lambda b: b.checked_in_date)
        beds_to_checkout = all_beds.filtered(lambda b: b.state != 'checked_out')
        if len(all_beds) == len(beds_to_checkout):
            folio.state = 'part_checked_out'
        self.state = 'checked_out'
        self.checked_out_date = fields.Datetime.now()
        # call folio checkout with last bed checkout
        if len(beds_to_checkout) == 1:
            folio.button_check_out()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Folio'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.folio',
            'res_id': folio.id,
            'target': 'new'
        }

    def compute_today_is_checkin(self):
        for rec in self:
            rec.today_is_checkin = False
            folio = rec.folio_id
            if folio.check_in_date and rec.state == 'draft':
                if folio.company_id.audit_date in [folio.check_in_date, (folio.check_in_date + relativedelta(days=1))]:
                    rec.today_is_checkin = True

    def compute_today_is_checkout(self):
        for rec in self:
            rec.today_is_checkout = False
            folio = rec.folio_id
            if folio.check_out_date and rec.state == 'checked_in':
                if folio.company_id.audit_date == folio.check_out_date:
                    rec.today_is_checkout = True
