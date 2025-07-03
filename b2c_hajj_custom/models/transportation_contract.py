from odoo import fields, models, api
from odoo.exceptions import ValidationError


class TransportationContract(models.Model):
    _name = 'transportation.contract'
    _rec_name = 'transportation_contract_no'

    transportation_company = fields.Many2one('res.partner', domain=[('is_transportation_company', '=', True)])
    no_buses = fields.Char('No. of Buses')
    transportation_contract_no = fields.Char("Transportation Contract No.")
    location_lines = fields.One2many('transportation.location.line', 'contract_id')
    pilgrims_no = fields.Integer(string='Pilgrims NO.')
    booked_no = fields.Integer(string='Booked NO.', compute='_compute_booked_no')
    available_no = fields.Integer(string='Available NO.', compute='_compute_available_no')

    @api.constrains('pilgrims_no', 'booked_no')
    def _check_booked_no(self):
        for record in self:
            if record.booked_no > record.pilgrims_no:
                raise ValidationError('Booked No. must be less than or equal to Pilgrims No.!')

    @api.depends('pilgrims_no', 'booked_no')
    def _compute_available_no(self):
        for record in self:
            if record.pilgrims_no > 0:
                record.available_no = record.pilgrims_no - record.booked_no
            else:
                record.available_no = 0

    def _compute_booked_no(self):
        for record in self:
            trans_contract_pilgrim = self.env['res.partner'].search([('transportation_contract_ids', 'in', record.id)])
            record.booked_no = len(trans_contract_pilgrim)
