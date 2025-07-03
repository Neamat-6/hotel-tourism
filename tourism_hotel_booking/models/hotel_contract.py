from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class HotelContract(models.Model):
    _inherit = "hotel.contract"

    account_invoice_id = fields.Many2one('account.move', 'Bill', readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('purchase', 'Purchase'), ('cancel', 'Cancelled')], 'State',
        default='draft', required=True, tracking=True)
    is_draft = fields.Boolean(default=False)
    start_date = fields.Date('Start Date', default=fields.Date.context_today)
    end_date = fields.Date('End Date', default=fields.Date.context_today)
    bill_total = fields.Float(compute="_compute_bill_total")
    invoice_ids = fields.One2many('account.move', 'hotel_contract_id')
    tax_id = fields.Many2one('account.tax', string='Taxes')
    contract_type = fields.Selection(selection=[('hotel', 'hotel'), ('transportation', 'Transportation')],
                                     default='hotel',
                                     string='Contract Type')
    transportation_type = fields.Selection(selection=[('plane', 'Planes'), ('bus', 'Buses')],
                                           string='Transportation Type')
    transportation_company = fields.Many2one('res.partner', domain="[('is_transportation_company', '=', True)]")
    plane_company = fields.Many2one('res.partner', domain="[('is_plane_company', '=', True)]")
    departure_date = fields.Datetime(string="Departure Date", required=False)
    return_date = fields.Datetime(string="Return Date", required=False)
    plane_contract_ids = fields.One2many('plane.contract.line', 'contract_id')
    transportation_contract_ids = fields.One2many('transportation.contract.line', 'contract_id')

    def action_open_bills(self):
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        action['domain'] = [('hotel_contract_id', '=', self.id), ('move_type', '=', 'in_invoice')]
        return action

    def _compute_bill_total(self):
        for rec in self:
            rec.bill_total = sum(rec.invoice_ids.filtered(lambda d: d.move_type == 'in_invoice').mapped('amount_total'))


    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.is_draft = True
            rec.account_invoice_id.button_draft()

    def action_update_bill(self):
        if self.contract_type == 'hotel':
            account_move_obj = self.account_invoice_id
            self.account_invoice_id.invoice_line_ids = [(5, 0, 0)]
            self.is_draft = False
            data = []
            for line in self.contract_line:
                data.append((0, 0, {
                    'name': line.room_type.name,
                    'price_unit': line.price,
                    'quantity': float(line.date_difference) * line.count,
                    'check_in': line.start_date,
                    'check_out': line.end_date,
                    'number_of_days': line.date_difference,
                    'account_id': self.hotel.journal_id.default_account_id.id,
                }))
            bill_create_obj = account_move_obj.sudo().update({
                'move_type': 'in_invoice',
                'partner_id': self.vendor.id,
                'ref': self.name,
                'date': fields.Date.today(),
                'invoice_date': fields.Date.today(),
                'journal_id': self.hotel.journal_id.id,
                'invoice_line_ids': data,
            })
            self.account_invoice_id.action_post()
            self.state = 'purchase'
            return {
                'name': 'account.move',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.account_invoice_id.id,
                'target': 'current',
                'type': 'ir.actions.act_window'
            }
        else:
            if self.transportation_type == 'plane':
                account_move_obj = self.account_invoice_id
                self.account_invoice_id.invoice_line_ids = [(5, 0, 0)]
                self.is_draft = False
                data = []
                for line in self.plane_contract_ids:
                    data.append((0, 0, {
                        'name': line.plane_type_id.name,
                        'price_unit': line.unit_price,
                        'quantity': line.number_of_seats,
                    }))
                bill_create_obj = account_move_obj.sudo().update({
                    'move_type': 'in_invoice',
                    'partner_id': self.vendor.id,
                    'ref': self.name,
                    'date': fields.Date.today(),
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': data,
                    'hotel_contract_id': self.id
                })
                self.account_invoice_id.action_post()
                self.state = 'purchase'
                return {
                    'name': 'account.move',
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'res_id': self.account_invoice_id.id,
                    'target': 'current',
                    'type': 'ir.actions.act_window'
                }
            else:
                account_move_obj = self.account_invoice_id
                self.account_invoice_id.invoice_line_ids = [(5, 0, 0)]
                self.is_draft = False
                data = []
                for line in self.transportation_contract_ids:
                    data.append((0, 0, {
                        'name': line.bus_type_id.name,
                        'price_unit': line.unit_price,
                        'quantity': line.duration,
                    }))
                bill_create_obj = account_move_obj.sudo().update({
                    'move_type': 'in_invoice',
                    'partner_id': self.vendor.id,
                    'ref': self.name,
                    'date': fields.Date.today(),
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': data,
                    'hotel_contract_id': self.id
                })
                self.account_invoice_id.action_post()
                self.state = 'purchase'
                return {
                    'name': 'account.move',
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'res_id': self.account_invoice_id.id,
                    'target': 'current',
                    'type': 'ir.actions.act_window'
                }


    def create_bill(self):
        if self.is_draft:
            self.action_update_bill()
        else:
            account_move_obj = self.env['account.move']
            data = []
            if self.contract_type == 'hotel':
                for line in self.contract_line:
                    if not line.account_move_id:
                        data.append((0, 0, {
                            'name': line.room_type.name,
                            'price_unit': line.price,
                            'quantity': float(line.date_difference) * line.count,
                            'check_in': line.start_date,
                            'check_out': line.end_date,
                            'number_of_days': line.date_difference,
                            'account_id': self.hotel.journal_id.default_account_id.id,
                        }))
                bill_create_obj = account_move_obj.create({
                    'move_type': 'in_invoice',
                    'partner_id': self.vendor.id,
                    'ref': self.name,
                    'date': fields.Date.today(),
                    'invoice_date': fields.Date.today(),
                    'journal_id': self.hotel.journal_id.id,
                    'invoice_line_ids': data,
                    'hotel_contract_id': self.id
                })
                bill_create_obj.action_post()
                self.account_invoice_id = bill_create_obj.id
                self.state = 'purchase'
                return {
                    'name': 'account.move',
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'res_id': bill_create_obj.id,
                    'target': 'current',
                    'type': 'ir.actions.act_window'
                }
            else:
                if self.transportation_type == 'plane':
                    for line in self.plane_contract_ids:
                        if not line.is_invoiced:
                            data.append((0, 0, {
                                'name': line.plane_type_id.name,
                                'price_unit': line.unit_price,
                                'quantity': line.number_of_seats,
                            }))
                    bill_create_obj = account_move_obj.create({
                        'move_type': 'in_invoice',
                        'partner_id': self.vendor.id,
                        'ref': self.name,
                        'date': fields.Date.today(),
                        'invoice_date': fields.Date.today(),
                        'invoice_line_ids': data,
                        'hotel_contract_id': self.id
                    })
                    bill_create_obj.action_post()
                    self.account_invoice_id = bill_create_obj.id
                    self.state = 'purchase'
                    return {
                        'name': 'account.move',
                        'res_model': 'account.move',
                        'view_mode': 'form',
                        'res_id': bill_create_obj.id,
                        'target': 'current',
                        'type': 'ir.actions.act_window'
                    }
                else:
                    for line in self.transportation_contract_ids:
                        if not line.is_invoiced:
                            data.append((0, 0, {
                                'name': line.bus_type_id.name,
                                'price_unit': line.unit_price,
                                'quantity': line.duration,
                            }))
                    bill_create_obj = account_move_obj.create({
                        'move_type': 'in_invoice',
                        'partner_id': self.vendor.id,
                        'ref': self.name,
                        'date': fields.Date.today(),
                        'invoice_date': fields.Date.today(),
                        'invoice_line_ids': data,
                        'hotel_contract_id': self.id
                    })
                    bill_create_obj.action_post()
                    self.account_invoice_id = bill_create_obj.id
                    self.state = 'purchase'
                    return {
                        'name': 'account.move',
                        'res_model': 'account.move',
                        'view_mode': 'form',
                        'res_id': bill_create_obj.id,
                        'target': 'current',
                        'type': 'ir.actions.act_window'
                    }

    def create_purchase_contract(self):
        invoice_obj = self.env['purchase.order']
        data = []
        for u in self.contract_line:
            data.append((0, 0, {
                'name': u.room_type.name,
                'product_id': u.room_type.product_id.id,
                'product_qty': u.count,
                'start_date': u.start_date,
                'end_date': u.end_date,
                'price_unit': u.price,
                'price_subtotal': u.total
            }))
        inv_create_obj = invoice_obj.create({
            'hotel': self.hotel.id,
            'partner_id': self.vendor.id,
            'tax_totals_json': self.total,
            'order_line': data
        })
        self.update({'invoice_id_con': inv_create_obj})
        self.state = 'purchase'
        return {
            'name': 'purchase.order.form',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': inv_create_obj.id,
            'target': 'current',
            'type': 'ir.actions.act_window'
        }

    # def create_purchase_contract(self):
    #     action = self.env.ref('purchase.action_rfq_form').read()[0]
    #     # action['domain'] = [('appointment_id', '=', self.id)]
    #     action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
    #     action['context'] = {
    #         'default_partner_id': self.vendor.id,
    #         'default_tax_totals_json': self.total,
    #         'default_order_line': [(6, 0, self.contract_line.ids)],
    #      }
    #     return action

    # def create_purchase_contract(self):
    #
    #     self.ensure_one()
    #     vals = {
    #         # 'origin': self.approval_request_id.name,
    #         'partner_id': self.vendor.id,
    #     }
    #     return vals
    def action_open_wizard(self):
        return {
            'name': 'Contract',
            'res_model': 'contract.wizard',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'default_contract_line_ids': self.contract_line.ids},
        }


class HotelContractLine(models.Model):
    _inherit = "hotel.contract.line"

    room_type = fields.Many2one('hotel.room', string="Room Type", required=True)
    count = fields.Float('Room Count')
    start_date = fields.Date('Start Date', default=fields.Date.context_today)
    end_date = fields.Date('End Date', default=fields.Date.context_today)
    new_start_date = fields.Date('Start Date')
    new_end_date = fields.Date('End Date')
    contract_id = fields.Many2one('hotel.contract')
    price = fields.Float('Price', digits=(12, 5))
    total = fields.Float('Total', compute='compute_total', store=True)
    date_difference = fields.Char(' Total Days', compute='time_function')
    new_date_difference = fields.Char('Days')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('purchase', 'Purchase'), ('cancel', 'Cancelled')],
        'State', related='contract_id.state', store=True)
    hotel_id = fields.Many2one('hotel.hotel', string='Hotel', related='contract_id.hotel', store=True)
    account_move_id = fields.Many2one('account.move', string='Bill')

    @api.depends('date_difference', 'count', 'price')
    def compute_total(self):
        for rec in self:
            rec.total = float(rec.date_difference) * float(rec.price) * rec.count

    @api.onchange('room_type')
    def _get_price(self):
        if self.room_type:
            self.price = self.room_type.price

    @api.onchange('start_date', 'end_date')
    def time_function(self):
        for record in self:
            d1 = record.start_date
            d2 = record.end_date
            time_diff = (d2 - d1).days
            record.date_difference = time_diff

    @api.onchange('new_start_date', 'new_end_date')
    def new_time_function(self):
        for record in self:
            if record.new_start_date and record.new_end_date:
                d1 = record.new_start_date
                d2 = record.new_end_date
                time_diff = (d2 - d1).days
                record.new_date_difference = time_diff

    def create_bill(self):
        account_move_obj = self.env['account.move']
        data = []
        for line in self:
            data.append((0, 0, {
                'name': line.room_type.name,
                'price_unit': line.price,
                'quantity': float(line.date_difference) * line.count,
                'check_in': line.start_date,
                'check_out': line.end_date,
                'number_of_days': line.date_difference,
            }))
        bill_create_obj = account_move_obj.create({
            'move_type': 'in_invoice',
            'partner_id': line.contract_id.vendor.id,
            'date': fields.Date.today(),
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': data,
            'hotel_contract_id': line.contract_id.id,
        })
        self.account_move_id = bill_create_obj.id


class PlaneContractLine(models.Model):
    _name = 'plane.contract.line'

    contract_id = fields.Many2one('hotel.contract')
    plane_type_id = fields.Many2one(comodel_name="plane.type", string="Plane Type")
    number_of_seats = fields.Integer("Seats Number")
    unit_price = fields.Float("Unit Price")
    total_amount = fields.Float("Total", compute='calc_total_amount')
    transportation_type = fields.Selection(related='contract_id.transportation_type')
    is_invoiced = fields.Boolean('Invoiced')

    @api.onchange('number_of_seats', 'unit_price')
    def calc_total_amount(self):
        for rec in self:
            if rec.number_of_seats and rec.unit_price:
                rec.total_amount = rec.number_of_seats * rec.unit_price
            else:
                rec.total_amount = 0.0


class TransportationContractLine(models.Model):
    _name = 'transportation.contract.line'

    contract_id = fields.Many2one('hotel.contract')
    bus_type_id = fields.Many2one(comodel_name="bus.type", string="Bus Type")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    duration = fields.Integer("Duration", compute='calc_duration')
    unit_price = fields.Float("Unit Price (Day)")
    total_amount = fields.Float("Total", compute='calc_total_amount')
    transportation_type = fields.Selection(related='contract_id.transportation_type')
    is_invoiced = fields.Boolean('Invoiced')

    @api.onchange('duration', 'unit_price')
    def calc_total_amount(self):
        for rec in self:
            if rec.duration and rec.unit_price:
                rec.total_amount = rec.duration * rec.unit_price
            else:
                rec.total_amount = 0.0

    @api.onchange('start_date', 'end_date')
    def calc_duration(self):
        self.duration = 0
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError("Start Date Greater Than End Date !")
                else:
                    rec.duration = (rec.end_date - rec.start_date).days
