# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('company_type')
    def get_access_creation(self):
        if self.env.user.has_group('hotel_booking.group_create_company'):
            self.has_access_company = True
        else:
            self.has_access_company = False

    has_access_company = fields.Boolean(compute='get_access_creation')
    national_id = fields.Char(string='National ID')
    person_arabic_name = fields.Char()
    company_arabic_name = fields.Char()
    passport_no = fields.Char(string='Passport ID')
    travel_type = fields.Selection(selection=[
        ('company', 'Travel Company'), ('agent', 'Travel Agent'),
    ], default='company')
    company_code = fields.Char(copy=False, readonly=True, index=True, default=lambda self: _('New'))
    online_travel_agent = fields.Boolean(string='Online Travel Agent')
    market_segmentation = fields.Boolean(string='Market Segmentation')
    market_segmentation_id = fields.Many2one('market.segmentation', string='Market Segmentation')
    is_city_ledger = fields.Boolean(string='City Ledger')
    birth_date = fields.Date()
    customer_credit_limit = fields.Monetary("Customer Credit Limit")
    customer_due_amount = fields.Monetary("Customer Due Amount", compute='calc_customer_due')
    balance = fields.Monetary("Balance", compute='calc_balance')
    total_advanced_payment = fields.Monetary("Total Advance Payment", readonly=True)
    is_credit_limit = fields.Boolean("Has Credit Limit")
    front_id = fields.Binary("Front ID")
    back_id = fields.Binary("Back ID")
    is_required_company = fields.Boolean(compute='_compute_company_fields')

    @api.onchange('company_type')
    def _compute_company_fields(self):
        for partner in self:
            if self.env.user.company_id.is_required_company:
                partner.is_required_company = True
            else:
                partner.is_required_company = False

    # def _write_company_type(self):
    #     for partner in self:
    #         if self.env.user.has_group('hotel_booking.group_create_company'):
    #             partner.is_company = partner.company_type == 'company'
    #         else:
    #             partner.is_company = False

    @api.onchange('customer_credit_limit')
    def _notify_credit_limit_change(self):
        for partner in self:
            if partner.customer_credit_limit:
                return {'warning': {
                    'title': _('Credit Limit Updated'),
                    'message': _(
                        f"Credit Limit has been Successfully Updated to {partner.customer_credit_limit} {self.env.company.currency_id.name}")
                }}

    @api.onchange('customer_credit_limit')
    def calc_customer_due(self):
        for rec in self:
            customer_due_amount = sum(
                self.env['hotel.booking'].search(['|', ('company_booking_source', '=', rec.id),('online_travel_agent_source', '=', rec.id)]).filtered(
                    lambda l: l.company_paid == 0.0).mapped('paid_amount_city_ledger'))
            if customer_due_amount:
                rec.customer_due_amount = customer_due_amount
            else:
                rec.customer_due_amount = 0

    @api.onchange('customer_credit_limit', 'customer_due_amount')
    def calc_balance(self):
        for rec in self:
            if rec.customer_credit_limit or rec.total_advanced_payment or rec.customer_due_amount:
                rec.balance = (rec.customer_credit_limit + rec.total_advanced_payment) - rec.customer_due_amount
            else:
                rec.balance = 0.0

    @api.constrains('company_type')
    def _check_company_type(self):
        for record in self:
            if record.company_type == 'person':
                record.travel_type = False

    def action_open_bookings(self):
        self.ensure_one()
        action = self.env.ref('hotel_booking.action_hotel_booking').read()[0]
        action['domain'] = [('partner_id', '=', self.id), ('state', '=', 'confirmed')]
        return action

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|', ('name', operator, name), ('email', operator, name), ('phone', operator, name),
                      ('company_code', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def create(self, values):
        if values.get('company_code', _('New')) == _('New') and values.get('travel_type', False):
            if values['travel_type'] == 'company':
                values['company_code'] = self.env['ir.sequence'].next_by_code('travel.company.sequence') or _('New')
        group_portal = self.env.ref('base.group_portal')
        partner = super(ResPartner, self).create(values)
        if 'create_user' in self._context:
            if not partner.email:
                raise UserError("Please add an email address.")
            user = self.env['res.users'].sudo().create({
                'partner_id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'login': partner.email,
                'company_id': self.env.company.id,
                'company_ids': [(6, 0, self.env.company.ids)],
                'groups_id': [(4, group_portal.id)]
            })
            try:
                user.action_reset_password()
            except:
                print("Cannot send reset email")
        return partner

    @api.onchange('country_id')
    def get_country_phone(self):
        for rec in self:
            if rec.country_id:
                rec.mobile = rec.country_id.phone_code
            else:
                rec.mobile = False

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            pass
