from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class PilgrimTransport(models.TransientModel):
    _name = 'pilgrim.transport'
    _description = 'Pilgrim Transportation'
    _rec_name = 'rec_name'

    minnah_camp = fields.Selection([
        ('المعيصم', 'المعيصم'),
        ('الحرس', 'الحرس'),
        ('مجر الكبش', 'مجر الكبش'),
    ], string='Minnah Camp', required=True)
    transport_type = fields.Selection([('bus', 'Bus'), ('train', 'Train')], string='Transport Type')
    rec_name = fields.Char(default='Pilgrim Transportation')
    pilgrim_no = fields.Integer(required=True)
    from_status = fields.Selection([('hotel_arfa', 'الانتقال من الفندق الي عرفة'), ('minnah_arrival', 'الوصول الي مني -تروية'),
                               ('minnah_arrival2', 'الوصول الي مني'), ('minnah_arfa', 'الانتقال من مني الى عرفة'),
                               ('arfa_arrival', 'الوصول الي عرفة'), ('arfa_mzdlfa', 'الانتقال من عرفة  الى مزدلفة'),
                               ('mzdlfa_minnah', 'الانتقال من مزدلفة الي مني'),('minnah_hotel', 'الانتقال من مني الي الفندق'),
                                 ('hotel_makkah_arrival', 'الوصول فندق مكه')],
                              string="From Status", required=True)
    to_status = fields.Selection([('hotel_arfa', 'الانتقال من الفندق الي عرفة'), ('minnah_arrival', 'الوصول الي مني -تروية'),
                               ('minnah_arrival2', 'الوصول الي مني'), ('minnah_arfa', 'الانتقال من مني الى عرفة'),
                               ('arfa_arrival', 'الوصول الي عرفة'), ('arfa_mzdlfa', 'الانتقال من عرفة  الى مزدلفة'),
                               ('mzdlfa_minnah', 'الانتقال من مزدلفة الي مني'),('minnah_hotel', 'الانتقال من مني الي الفندق'),
                                 ('hotel_makkah_arrival', 'الوصول فندق مكه')],
                              string="To Status", required=True)
    pilgrim_ids = fields.Many2many('res.partner', string="Pilgrims", compute='_compute_pilgrim_ids')
    makkah_hotel = fields.Many2one('hotel.hotel', domain=[('type', '=', 'makkah')], string='Makkah Hotel')

    @api.onchange('transport_type')
    def _onchange_transport_type(self):
        if self.transport_type == 'bus':
            self.pilgrim_no = 47
        else:
            self.pilgrim_no = 1

    @api.depends('minnah_camp', 'from_status', 'makkah_hotel')
    def _compute_pilgrim_ids(self):
        for record in self:
            domain = [('main_minnah.name', '=', record.minnah_camp), ('status', '=', record.from_status)]
            if record.makkah_hotel:
                domain.append(('main_makkah', '=', record.makkah_hotel.id))
            record.pilgrim_ids = self.env['res.partner'].search(domain)


    def action_update_status(self):
        if not self.pilgrim_no:
            raise UserError(_('Pilgrim No. is required!'))

        if not self.pilgrim_ids:
            raise UserError(_('No Pilgrims Found!'))

        pilgrims_to_update = self.pilgrim_ids[:self.pilgrim_no]

        for pilgrim in pilgrims_to_update:
            pilgrim.with_user(self.env.user).write({'status': self.to_status})
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': 'Success',
        #         'message': 'Status updated successfully.',
        #         'type': 'success',
        #         'sticky': False,
        #     }
        # }

