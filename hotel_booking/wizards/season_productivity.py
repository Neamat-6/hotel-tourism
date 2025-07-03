from odoo import fields, models, _


class SeasonProductivity(models.TransientModel):
    _name = 'season.productivity'
    _description = 'Season Productivity Report'

    line_ids = fields.One2many('season.productivity.line', 'wizard_id')
    booking_source = fields.Selection(
        selection=[('online_agent', 'Online Travel Agent'), ('company', 'Company'), ('direct', 'Direct')])
    online_travel_agent_source = fields.Many2one('res.partner', domain="[('online_travel_agent', '=', True)]")
    company_booking_source = fields.Many2one('res.partner', domain="[('is_company','=',True)]")
    season_ids = fields.Many2many('season.duration', string='Season')
    hotel_ids = fields.Many2many("hotel.hotel", string="Hotel")

    def get_booking_source_folios(self):
        self.line_ids = [(5, 0, 0)]  # Clear existing lines
        domain = [('state', '!=', 'cancelled')]

        # Filter by selected hotels
        if self.hotel_ids:
            domain.append(('hotel_id', 'in', self.hotel_ids.ids))

        # Filter by booking source
        if self.booking_source:
            domain.append(('booking_source', '=', self.booking_source))

            if self.booking_source == 'online_agent' and self.online_travel_agent_source:
                domain.append(('online_travel_agent_source', '=', self.online_travel_agent_source.id))

            elif self.booking_source == 'company':
                if self.company_booking_source:
                    domain.append(('company_booking_source', '=', self.company_booking_source.id))
                else:
                    company_ids = self.env['res.partner'].search([('is_company', '=', True)]).ids
                    domain.append(('company_booking_source', 'in', company_ids))

        # Conditionally filter by seasons
        if self.season_ids:
            season_ids = self.season_ids.ids
            domain.append(('season_id', 'in', season_ids))
        else:
            season_ids = self.env['season.duration'].search([]).ids

        hotel_booking_objs = self.env['hotel.booking'].search(domain)

        season_totals = {season_id: {'total_amount': 0} for season_id in season_ids}

        # Accumulate totals for bookings based on seasons
        for booking in hotel_booking_objs:
            season_id = booking.season_id.id
            total_amount = booking.amount_total

            if season_id in season_totals:
                season_totals[season_id]['total_amount'] += total_amount

        for season_id, totals in season_totals.items():
            self.env['season.productivity.line'].create({
                'wizard_id': self.id,
                'season_id': season_id,
                'total_amount': totals['total_amount'],
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Season Productivity'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'season.productivity',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_season_productivity_report').with_context(
            landscape=True).report_action(self)

    def print_xlsx(self):
        return self.env.ref('hotel_booking.action_season_productivity_report_xlsx').report_action(self)


class SeasonProductivityLine(models.TransientModel):
    _name = 'season.productivity.line'
    _description = 'Season Productivity Line'

    wizard_id = fields.Many2one('season.productivity')
    season_id = fields.Many2one('season.duration')
    total_amount = fields.Float(string='Total Amount')
    total_paid = fields.Float(string='Total Paid')
    total_discount = fields.Float(string='Total Discount')
