from odoo import fields, models, api


class ScanPilgrimWizard(models.TransientModel):
    _name = 'scan.pilgrim.wizard'
    _description = 'Scan Pilgrim Wizard'
    _rec_name = 'rec_name'

    status = fields.Selection([('in_source_country', 'في بلد القدوم'),
                               ('jaddah_air_arrival', 'مطار جده - وصول'),('jaddah_air_departure', 'مطار جده - مغادره'),
                               ('madinah_air_arrival', 'مطار المدينة -  وصول'), ('madinah_air_departure', 'مطار المدينة - للمغادرة'),
                               ('airport_makkah', 'الانتقال من المطار الي فندق مكة '),
                               ('madinah_airport', 'الانتقال الي المطار من فندق المدينة'), ('makah_airport', 'الانتقال الي المطار من فندق مكه'),
                               ('hotel_arfa', 'الانتقال من الفندق الي عرفة'), ('minnah_arrival', 'الوصول الي مني -تروية'),
                               ('minnah_arrival2', 'الوصول الي مني'), ('minnah_arfa', 'الانتقال من مني الى عرفة'),
                               ('arfa_arrival', 'الوصول الي عرفة'), ('arfa_mzdlfa', 'الانتقال من عرفة  الى مزدلفة'),
                               ('mzdlfa_minnah', 'الانتقال من مزدلفة الي مني'),('minnah_hotel', 'الانتقال من مني الي الفندق'),
                                 ('hotel_makkah_arrival', 'الوصول فندق مكه'), ('hotel_makkah_departure', 'المغادرة فندق مكه'),
                               ('hotel_madinah_arrival', 'الوصول فندق المدينة'), ('hotel_madinah_departure', 'المغادرة فندق المدينة')],
                               string="Set Status", required=True)

    line_ids = fields.One2many('scan.pilgrim.line', 'wizard_id', string="Scanned Pilgrims")
    rec_name = fields.Char(default='Scan Pilgrims')

    def action_update_status(self):
        for line in self.line_ids:
            if line.partner_id:
                line.partner_id.write({'status': self.status})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Status updated successfully.',
                'type': 'success',
                'sticky': False,
            }
        }

class ScanPilgrimLine(models.TransientModel):
    _name = 'scan.pilgrim.line'

    wizard_id = fields.Many2one('scan.pilgrim.wizard', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Pilgrim")
    mobile = fields.Char(related='partner_id.mobile', string="Mobile")
    email = fields.Char(related='partner_id.email')
    pilgrim_id = fields.Char(related='partner_id.pilgrim_id')
    main_makkah = fields.Many2one('hotel.hotel', related='partner_id.main_makkah', string="Makkah Hotel")
    main_madinah = fields.Many2one('hotel.hotel', "Madinah Hotel", related='partner_id.main_madinah')
    makkah_room = fields.Many2one('hotel.room', string="Makkah Room", related='partner_id.makkah_room')
    madinah_room = fields.Many2one('hotel.room', string="Madinah Room", related='partner_id.madinah_room')




