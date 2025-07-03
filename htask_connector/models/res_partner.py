# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class HTaskGuest(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "abstract.htask.model"]

    _htask_type = "guest"

    _field_list_prevent_overwrite = ["name", "website", "email", "image_1920"]
    _field_list_required = ["name"]
    _field_list_many2one = {
        'country_id': 'res.country', 
        'nationality': 'res.country', 
        'birth_country': 'res.country', 
        'state_id': 'res.country.state'
    }

    guest_type = fields.Char(string='Guest Type')
    gender = fields.Char(string='Gender')
    vip_status = fields.Char(string='VIP Status')

    full_addr = fields.Char(string='Full Address')
    fax = fields.Char(string='Fax')

    nationality = fields.Many2one('res.country', string='Nationality')
    nationality_str = fields.Char(string='Nationality Str')
    
    country_str = fields.Char(string='Country Str')
    state_str = fields.Char(string='State Str')

    id_type = fields.Char(string='ID Type')
    id_no = fields.Char(string='ID No')
    id_expiry_date = fields.Date(string='Expiry Date')

    birth_city = fields.Char(string='Birth City')
    birth_country = fields.Many2one('res.country', string='Birth Country')
    birth_country_str = fields.Char(string='Birth Country Str')

    spouse_birth_date = fields.Date(string='Spouse Birth Date')

    reg_no = fields.Char(string='Registration No')

    is_blacklisted = fields.Boolean(string='Blacklisted')
    blacklist_reason = fields.Char(string='Blacklist Reason')

    source_ids = fields.Many2many('res.partner.source', string='Sources')
    is_guest = fields.Boolean(string='Is Guest')
    is_hotel_customer = fields.Boolean(string='Is Hotel Customer')
    is_city_ledger_customer = fields.Boolean(string='Is City Ledger Customer')

    @api.model
    def get_conversion_dict(self):
        res = super().get_conversion_dict()
        res.update({
            # "htask_id_external": "Id",
            "name": "Contact_person",
            "guest_type": "Type",
            "gender": "Gender",
            "vip_status": "VIPStatus",
            "full_addr": "Address",  # full address
            "city": "City",
            "zip": "PostalCode",
            "state_id": "State",  # state_id.name
            "state_str": "State",  # state_id.name
            "country_id": "Country",  # country_id.name
            "country_str": "Country",  # country_id.name
            "phone": "Phone",
            "mobile": "Mobile",
            "fax": "Fax",
            "nationality": "Nationality",  # Same as country name
            "nationality_str": "Nationality",  # Same as country name
            "settlement_by": "SettlementBy",
            "direct_billing_account": "DirectBillingAccount",
            "id_type": "IDType",
            "id_no": "IDNo",
            "id_expiry_date": "ExpiryDate",
            "birth_city": "BirthCity",
            "birth_country": "BirthCountry",
            "birth_country_str": "BirthCountry",
            "spouse_birth_date": "SpouseBirthdate",
            "reg_no": "RegistrationNo",
            "is_blacklisted": "IsBlackListed",
            "blacklist_reason": "BlackListedReason",
        })
        return res

    # Action section
    def button_sync_guest(self):
        htask_guest = self.get_htask_connector(self._htask_type)
        Partner = self.env["res.partner"]
        travel_request_params = {
            "RES_Request": {
                "Request_Type": "TravelAgentList",
                "Authentication": {
                    "HotelCode": htask_guest.hotel_code,
                    "AuthCode": htask_guest.auth_code
                }
            }
        }
        res = htask_guest.get_post(arguments={}, data=travel_request_params)
        agents = res['TravelAgent']
        agent_dict = {}
        for agent in agents:
            agent_vals = {
                'name': agent['AccountName'],
                'htask_id_external': agent['Id'],
                'email': agent['Email'],
                'phone': agent['Phone'],
                'company_type': 'company'
            }
            agent_id = self.env['res.partner'].create(agent_vals)
            agent_dict[agent['AccountName']] = agent_id.id
        request_params = {
            "RES_Request": {
                "Request_Type": "GuestList",
                "Authentication": {
                    "HotelCode": htask_guest.hotel_code,
                    "AuthCode": htask_guest.auth_code
                }
            }
        }
        Guest = htask_guest.get_post(arguments={}, data=request_params)
        Guests = Guest['Guests']
        null_datetime = '0000-00-00 00:00:00'
        for guest_rec in Guests:
            vals = {'is_guest': True}
            if guest_rec['SpouseBirthdate'] == null_datetime:
                guest_rec['SpouseBirthdate'] = ''
            if guest_rec['ExpiryDate'] == null_datetime:
                guest_rec['ExpiryDate'] = ''
            if guest_rec['DirectBillingAccount']and guest_rec['DirectBillingAccount'] in agent_dict.keys():
                vals.update({'parent_id': agent_dict[guest_rec['DirectBillingAccount']]})
            Partner.get_from_id_or_create("Id", guest_rec, vals)

    def full_update(self):
        self.button_sync_guest()

    @api.model
    def cron_update_guest_list(self):
        self.button_sync_guest()
        return True

class HTaskGuestSource(models.Model):
    _name = "res.partner.source"

    name = fields.Char(string='Name')
