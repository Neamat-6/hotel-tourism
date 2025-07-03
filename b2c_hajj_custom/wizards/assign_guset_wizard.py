from odoo import fields, models, api


class AssignGuestWizard(models.TransientModel):
    _name = 'assign.guest.wizard'
    _description = 'Complete Gust Info'



    line_ids = fields.One2many('assign.guest.wizard.line', 'wizard_id')
    info_type = fields.Selection(selection=[
        ('gender', 'gender'), ('pilgrim_type', 'pilgrim_type'), ('member', 'member')
    ])

    def button_confirm(self):
        if self.info_type == 'gender':
            for line in self.line_ids:
                line.partner_id.write({'gender': line.gender})
        elif self.info_type == 'pilgrim_type':
            for line in self.line_ids:
                line.partner_id.write({'pilgrim_type': line.pilgrim_type})
        else:
            for line in self.line_ids:
                line.partner_id.sudo().write({'main_member_id': line.main_member_id.id})



class AssignGuestWizardLine(models.TransientModel):
    _name = 'assign.guest.wizard.line'
    _description = 'Complete Gust Info'

    wizard_id = fields.Many2one('assign.guest.wizard')
    partner_id = fields.Many2one('res.partner')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    pilgrim_type = fields.Selection(selection=[
        ('main', 'Main'), ('member', 'Family Member')
    ])
    main_member_id = fields.Many2one('res.partner')
    package_id = fields.Many2one('booking.package', related='partner_id.package_id')
    makkah_room_type = fields.Selection(related='partner_id.makkah_room_type')