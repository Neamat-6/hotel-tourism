from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class Folio(models.Model):
    _inherit = 'booking.folio'

    def write(self, vals):
        res = super(Folio, self).write(vals)
        if self.company_id.related_hotel_id.enable_umraheasy:
            cancel = False
            confirm = False
            if vals.get('state', False):
                if vals['state'] == 'cancelled':
                    cancel = True
                elif vals['state'] == 'confirmed':
                    confirm = True
            if vals.get('check_in', False) or vals.get('check_out', False) or vals.get('room_type_id', False) or cancel or confirm:
                if vals.get('room_type_id', False):
                    room_type_ids = [(6, 0, [vals['room_type_id']])]
                else:
                    room_type_ids = [(6, 0, self.room_type_id.ids)]

                if vals.get('check_in', False):
                    date_from = fields.Datetime.from_string(vals['check_in'])
                    if vals.get('check_out', False):
                        date_to = fields.Datetime.from_string(vals['check_out'])
                    elif vals.get('total_nights', False):
                        date_to = date_from + relativedelta(days=vals['total_nights'])
                    else:
                        date_to = date_from + relativedelta(days=1)
                elif vals.get('check_out', False):
                    date_to = fields.Datetime.from_string(vals['check_out'])
                    if vals.get('total_nights', False):
                        date_from = date_to - relativedelta(days=vals['total_nights'])
                    else:
                        date_from = self.check_in_date
                else:
                    date_from = self.check_in_date
                    date_to = self.check_out_date

                date_to -= relativedelta(days=1)

                wizard = self.env['umraheasy.connector'].create({
                    'date_from': date_from,
                    'date_to': date_to,
                    'action_type': 'update_inventory',
                    'company_id': self.company_id.id,
                    'room_type_ids': room_type_ids,
                    'folio_id': self.id
                })
                wizard.button_search()
                wizard.button_update_inventory()
        return res
