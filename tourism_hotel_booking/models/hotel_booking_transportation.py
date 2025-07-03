from odoo import models, fields, api,_


class HotelBookingTransportation(models.Model):
    _name = "hotel.booking.transportation"
    _description = "Hotel Booking Transportation"

    name = fields.Char(string="Name", default=lambda self: _('New'), readonly=True)
    customer_package_id = fields.Many2one(
        'hotel.transport.package',
        string="Customer Package",
        domain="[('id', 'in', customer_available_package_ids)]"
    )

    travel_agent_package_id = fields.Many2one(
        'hotel.transport.package',
        string="Travel Agent Package",
        domain="[('id', 'in', travel_agent_available_package_ids)]"
    )

    customer_available_package_ids = fields.Many2many(
        'hotel.transport.package',
        compute='_compute_customer_available_packages',
        store=False
    )

    travel_agent_available_package_ids = fields.Many2many(
        'hotel.transport.package',
        compute='_compute_travel_agent_available_packages',
        store=False
    )

    transportation_destination_lines = fields.One2many(
        'hotel.booking.transportation.destination.line',
        'hotel_booking_transportation_destination_id',
        string="Transportation Lines"
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        default=lambda self: self.env.company.hotel_default_customer_id.id
    )

    travel_agent_name = fields.Many2one('res.partner', string='Travel Agent Name')

    travel_agent_hotel_transportation_contract_id = fields.Many2one(
        'hotel.transportation.contract',
        string="Travel Agent Transportation Contract",
        domain="[('contract_type', '=', 'purchase')]"
    )

    customer_hotel_transportation_contract_id = fields.Many2one(
        'hotel.transportation.contract',
        string="Customer Transportation Contract",
        domain="[('contract_type', '=', 'sell')]"
    )

    makkah_hotel = fields.Char(string="Makkah Hotel")
    madinah_hotel = fields.Char(string="Madinah Hotel")
    makkah_arrival_date = fields.Datetime(string="Makkah Arrival Date")
    makkah_departure_date = fields.Datetime(string="Makkah Departure Date")
    madinah_arrival_date = fields.Datetime(string="Madinah Arrival Date")
    madinah_departure_date = fields.Datetime(string="Madinah Departure Date")
    flight_arrival_date = fields.Datetime(string="Flight Arrival Date")
    flight_departure_date = fields.Datetime(string="Flight Departure Date")
    arrival_flight_number = fields.Char(string="Arrival Flight Number")
    departure_flight_number = fields.Char(string="Departure Flight Number")

    total_cost_tax = fields.Float(compute='_compute_cost_totals', string='Total Cost With Tax', store=True)
    total_income = fields.Float(compute='_compute_cost_totals', string='Total Income With Tax', store=True)
    total_purchase_taxes = fields.Float(compute='_compute_cost_totals', store=True)
    total_sales_taxes = fields.Float(compute='_compute_cost_totals', store=True)
    difference = fields.Float(compute='_compute_cost_totals', store=True)
    supervisor = fields.Char("Supervisor")
    phone = fields.Char("Phone Number")
    number_of_guests = fields.Integer("Number Of Guests")
    operation_number = fields.Char("Operation Number")
    circular_number = fields.Char("Circular Number")

    transportation_booking_ids = fields.One2many('transportation.booking', 'hotel_booking_transportation_id')
    total_billed_amount = fields.Float('Total Billed Amount', compute='_compute_total_billed_amount')
    total_invoiced_amount = fields.Float('Total Invoiced Amount', compute='_compute_total_invoiced_amount')

    @api.depends('transportation_booking_ids')
    def _compute_total_billed_amount(self):
        for hotel_booking in self:
            hotel_booking.total_billed_amount = sum(hotel_booking.transportation_booking_ids.mapped('account_move_id').mapped('amount_total'))

    @api.depends('transportation_booking_ids')
    def _compute_total_invoiced_amount(self):
        for hotel_booking in self:
            hotel_booking.total_invoiced_amount = sum(hotel_booking.transportation_booking_ids.mapped('account_move').mapped('amount_total'))

    def action_print_transportation(self):
        return self.env.ref('hotel_booking.action_transportation_report').report_action(self, config=False)


    @api.onchange('travel_agent_name')
    def _onchange_travel_agent_name(self):
        if self.travel_agent_name:
            return {
                'domain': {
                    'travel_agent_hotel_transportation_contract_id': [
                        ('contract_type', '=', 'purchase'),
                        ('travel_agent_name', '=', self.travel_agent_name.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'travel_agent_hotel_transportation_contract_id': []
                }
            }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            return {
                'domain': {
                    'customer_hotel_transportation_contract_id': [
                        ('contract_type', '=', 'sell'),
                        ('partner_id', '=', self.partner_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'customer_hotel_transportation_contract_id': []
                }
            }

    @api.depends('transportation_booking_ids.cost_price',
                 'transportation_booking_ids.sell_price',
                 'transportation_booking_ids.no_of_bus',
                 'transportation_booking_ids.tax_ids')
    def _compute_cost_totals(self):
        for rec in self:
            total_cost_tax = 0.0
            total_income = 0.0
            total_purchase_taxes = 0.0
            total_sales_taxes = 0.0

            for line in rec.transportation_booking_ids:
                if line.purchase_tax_ids:
                    purchase_taxes = line.purchase_tax_ids.compute_all(
                        line.cost_price * line.no_of_bus,
                        currency=self.env.company.currency_id
                    )
                    total_cost_tax += purchase_taxes['total_included']
                    total_purchase_taxes += purchase_taxes['total_included'] - purchase_taxes['total_excluded']
                else:
                    total_cost_tax += line.cost_price * line.no_of_bus

                if line.sales_tax_ids:
                    sales_taxes = line.sales_tax_ids.compute_all(
                        line.sell_price * line.no_of_bus,
                        currency=self.env.company.currency_id
                    )
                    total_income += sales_taxes['total_included']
                    total_sales_taxes += sales_taxes['total_included'] - sales_taxes['total_excluded']
                else:
                    total_income += line.sell_price * line.no_of_bus

            rec.total_cost_tax = total_cost_tax
            rec.total_income = total_income
            rec.total_purchase_taxes = total_purchase_taxes
            rec.total_sales_taxes = total_sales_taxes
            rec.difference = total_income - total_cost_tax

    @api.onchange('transportation_booking_ids')
    def _onchange_transportation_booking(self):
        self._compute_cost_totals()

    @api.onchange('customer_package_id', 'travel_agent_package_id')
    def _onchange_package_id(self):
        self.transportation_booking_ids = [(5, 0, 0)]
        self.transportation_destination_lines = [(5, 0, 0)]

        if not self.customer_package_id and not self.travel_agent_package_id:
            return

        transportation_lines = []
        destination_lines = []
        travel_contract = self.travel_agent_hotel_transportation_contract_id
        customer_contract = self.customer_hotel_transportation_contract_id
        travel_cost_price = 0.0
        customer_sell_price = 0.0

        if travel_contract:
            travel_contract_line = travel_contract.hotel_transportation_contract_lines.filtered(
                lambda l: l.package_id.id == self.travel_agent_package_id.id)
            if travel_contract_line:
                travel_cost_price = travel_contract_line[0].price

        if customer_contract:
            customer_contract_line = customer_contract.hotel_transportation_contract_lines.filtered(
                lambda l: l.package_id.id == self.customer_package_id.id)
            if customer_contract_line:
                customer_sell_price = customer_contract_line[0].price

        selected_package = self.customer_package_id or self.travel_agent_package_id

        first_line = selected_package.transport_package_lines[:1]
        if first_line:
            transportation_lines.append((0, 0, {
                'customer_package_id': selected_package.id,
                'product_id': first_line.product_id.id if hasattr(first_line, 'product_id') else False,
                'departure_date': fields.Datetime.now(),
                'return_date': fields.Datetime.now(),
                'no_of_bus': 1,
                'no_of_passengers': 50,
                'cost_price': travel_cost_price,
                'sell_price': customer_sell_price,
            }))
            for line in selected_package.transport_package_lines:
                destination_lines.append((0, 0, {
                    'from_destination_id': line.from_destination_id.id,
                    'to_destination_id': line.to_destination_id.id,
                    'datetime': fields.Datetime.now(),
                    'state': False,
                    'move': 'arrival',
                }))

        self.transportation_booking_ids = transportation_lines
        self.transportation_destination_lines = destination_lines
        self._compute_cost_totals()

    @api.depends('customer_hotel_transportation_contract_id')
    def _compute_customer_available_packages(self):
        for rec in self:
            customer_available_packages = set()
            if rec.travel_agent_hotel_transportation_contract_id:
                customer_available_packages.update(
                    rec.travel_agent_hotel_transportation_contract_id.hotel_transportation_contract_lines.mapped('package_id.id')
                )
            if rec.customer_hotel_transportation_contract_id:
                customer_available_packages.update(
                    rec.customer_hotel_transportation_contract_id.hotel_transportation_contract_lines.mapped('package_id.id')
                )
            rec.customer_available_package_ids = [(6, 0, list(customer_available_packages))] if customer_available_packages else [(5, 0, 0)]

    @api.depends('travel_agent_hotel_transportation_contract_id')
    def _compute_travel_agent_available_packages(self):
        for rec in self:
            travel_agent_available_packages = set()
            if rec.travel_agent_hotel_transportation_contract_id:
                travel_agent_available_packages.update(
                    rec.travel_agent_hotel_transportation_contract_id.hotel_transportation_contract_lines.mapped('package_id.id')
                )
            if rec.customer_hotel_transportation_contract_id:
                travel_agent_available_packages.update(
                    rec.customer_hotel_transportation_contract_id.hotel_transportation_contract_lines.mapped('package_id.id')
                )
            rec.travel_agent_available_package_ids = [(6, 0, list(travel_agent_available_packages))] if travel_agent_available_packages else [(5, 0, 0)]

    def action_open_bills(self):
      action = self.env.ref('account.action_move_in_invoice_type').read()[0]
      account_move_ids = self.transportation_booking_ids.mapped('account_move_id').ids
      action['domain'] = [('id', 'in', account_move_ids)]
      return action

    def action_open_invoices(self):
      action = self.env.ref('account.action_move_out_invoice_type').read()[0]
      account_move_ids = self.transportation_booking_ids.mapped('account_move').ids
      action['domain'] = [('id', 'in', account_move_ids)]
      return action

    @api.model_create_multi
    def create(self, vals_list):
      for vals in vals_list:
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.booking.transportation') or _('New')
      return super().create(vals_list)

class HotelBookingTransportationDestinationLine(models.Model):
    _name = "hotel.booking.transportation.destination.line"
    _description = "Hotel Booking Transportation Destination Line"

    hotel_booking_transportation_destination_id = fields.Many2one(
        'hotel.booking.transportation',
        string="Transportation",
        required=True,
        ondelete="cascade"
    )
    from_destination_id = fields.Many2one('hotel.destination', string="From Destination", required=True)
    to_destination_id = fields.Many2one('hotel.destination', string="To Destination", required=True)
    datetime = fields.Datetime(string="Datetime", default=fields.Datetime.now)
    state = fields.Boolean(string="State")
    move = fields.Selection([('arrival', 'Arrival'), ('visits', 'Visits'), ('internal', 'Internal'), ('departure', 'Departure')], string="Move")