from odoo import fields, models, api


class TourismHotelBooking(models.Model):
    _inherit = 'tourism.hotel.booking'

    crm_lead_id = fields.Many2one('crm.lead', string='CRM Lead', ondelete='cascade', index=True, help="Link to the CRM lead associated with this booking.")


class PilgrimBooking(models.Model):
    _inherit = 'pilgrim.booking'

    crm_lead_id = fields.Many2one('crm.lead', string='CRM Lead', ondelete='cascade', index=True, help="Link to the CRM lead associated with this booking.")



class CrmLead(models.Model):
    _inherit = 'crm.lead'

    tourism_hotel_booking_ids = fields.One2many('tourism.hotel.booking', 'crm_lead_id', string='Tourism Bookings')
    tourism_hotel_booking_count = fields.Integer(compute='_compute_tourism_hotel_booking_count', string='Tourism Booking Count')
    package_booking_ids = fields.One2many('pilgrim.booking', 'crm_lead_id', string='Package Bookings')
    package_booking_count = fields.Integer(compute='_compute_package_booking_count', string='Package Booking Count')

    @api.depends('tourism_hotel_booking_ids')
    def _compute_tourism_hotel_booking_count(self):
        for lead in self:
            lead.tourism_hotel_booking_count = len(lead.tourism_hotel_booking_ids)

    @api.depends('package_booking_ids')
    def _compute_package_booking_count(self):
        for lead in self:
            lead.package_booking_count = len(lead.package_booking_ids)

    def action_view_tourism_hotel_bookings(self):
        action = self.env["ir.actions.actions"]._for_xml_id("tourism_hotel_booking.action_hotel_booking")
        action['domain'] = [('crm_lead_id', '=', self.id)]
        action['context'] = {
            'default_crm_lead_id': self.id,
            'search_default_crm_lead_id': self.id,
        }
        return action

    def action_view_package_bookings(self):
        action = self.env["ir.actions.actions"]._for_xml_id("b2c_hajj_custom.action_pilgrim_booking_view")
        action['domain'] = [('crm_lead_id', '=', self.id)]
        action['context'] = {
            'default_crm_lead_id': self.id,
            'search_default_crm_lead_id': self.id,
        }
        return action

    def action_pilgrim_booking_new(self):
        if not self.partner_id:
            action = self.env["ir.actions.actions"]._for_xml_id("hotel_booking_crm.crm_booking_partner_action")
            action['context'] = {'default_booking_type': 'package'}
            return action
        else:
            return self.action_pilgrim_booking()

    def action_tourism_booking_new(self):
        if not self.partner_id:
            action = self.env["ir.actions.actions"]._for_xml_id("hotel_booking_crm.crm_booking_partner_action")
            action['context'] = {'default_booking_type': 'tourism'}
            return action
        else:
            return self.action_tourism_booking()


    def action_pilgrim_booking(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pilgrim Booking',
            'res_model': 'pilgrim.booking',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_crm_lead_id': self.id,
                'default_source': 'person',
                'default_partner_id': self.partner_id.id,
                'default_company_id': self.company_id.id or self.env.company.id,
            }
        }


    def action_tourism_booking(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tourism Booking',
            'res_model': 'tourism.hotel.booking',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_crm_lead_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_company_id': self.company_id.id or self.env.company.id,

            }
        }

    def action_create_customer_new(self):
        """
        Create a new partner from the lead and open its form view.
        If partner already exists, open the existing partner form.
        """
        self.ensure_one()
        
        # Create partner if not exists
        if not self.partner_id:
            # Create the partner first
            self._handle_partner_assignment(create_missing=True)
            # Refresh the record to get the created partner
            self.refresh()
        if not self.partner_id:
            return {'type': 'ir.actions.act_window_close'}
            
        # Return the action to open the partner form
        return {
            'name': 'Customer',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,  # Use the created partner's ID
            'view_mode': 'form',
            'view_id': self.env.ref('base.view_partner_form').id,
            'target': 'current',  # Open in the same tab
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
        }