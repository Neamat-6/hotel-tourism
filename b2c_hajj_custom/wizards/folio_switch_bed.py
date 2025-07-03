from odoo import fields, models, api


class FolioSwitchBed(models.TransientModel):
    _name = 'folio.switch.bed'
    _description = 'Folio Switch Bed'

    allowed_guest_ids = fields.Many2many('booking.guest')
    guest1 = fields.Many2one('booking.guest')
    guest2 = fields.Many2one('booking.guest', domain="[('id', 'in', allowed_guest_ids)]")
    allowed_room_ids = fields.Many2many('hotel.room')
    room_id = fields.Many2one('hotel.room', domain="[('id', 'in', allowed_room_ids)]")

    @api.onchange('room_id')
    def _onchange_hotel_id(self):
        """ Dynamically filter floors based on the selected hotel """
        if self.room_id:
            return {'domain': {'guest2': [('id', 'in', self.allowed_guest_ids.ids),('room_id','=',self.room_id.id)]}}
        else:
            return {'domain': {'guest2': [('id', 'in', self.allowed_guest_ids.ids)]}}

    def button_switch(self):
        guest1 = self.guest1
        guest2 = self.guest2
        folio1 = guest1.folio_id
        folio2 = guest2.folio_id
        bed1 = folio1.bed_ids.filtered(lambda b: b.partner_id.id == guest1.partner_id.id)
        bed2 = folio2.bed_ids.filtered(lambda b: b.partner_id.id == guest2.partner_id.id)
        self.guest1.write({'folio_id': folio2})
        self.guest2.write({'folio_id': folio1})
        bed1.write({'partner_id': guest2.partner_id.id})
        bed2.write({'partner_id': guest1.partner_id.id})