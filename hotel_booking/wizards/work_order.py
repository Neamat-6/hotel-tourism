from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class WorkOrder(models.TransientModel):
    _name = 'work.order'
    _description = 'Work Order'

    line_ids = fields.One2many('work.order.line', 'wizard_id')
    order_type = fields.Selection(selection=[('immediate', 'Immediate'), ('advance', 'Advance')])
    date_start = fields.Datetime()
    date_stop = fields.Datetime()
    date_deadline = fields.Datetime()
    room_id = fields.Many2one('hotel.room')
    employee_id = fields.Many2one('hr.employee')
    employee_ids = fields.Many2many('hr.employee')
    type = fields.Selection(selection=[
        ('fix', 'Fix'),
        ('maintenance', 'Maintenance'),
        ('clean', 'Clean'),
        ('other', 'Other'),
    ])
    priority = fields.Selection(selection=[
        ('high', 'High'),
        ('low', 'Low'),
        ('manual', 'Manual'),
    ])
    state = fields.Selection(selection=[
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('progress', 'Progress'),
        ('done', 'Done'),
    ])
    department_id = fields.Many2one('hr.department')

    @api.onchange('department_id')
    def get_employee(self):
        if self.department_id:
            self.employee_ids = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])
        else:
            self.employee_ids = False
            self.employee_id = False

    def get_work_order(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        order_type = self.order_type
        date_start = self.date_start
        date_stop = self.date_stop
        date_deadline = self.date_deadline
        room_id = self.room_id
        employee_id = self.employee_id
        type = self.type
        priority = self.priority
        state = self.state
        department_id = self.department_id
        if order_type:
            domain.append(('order_type', '=', order_type))
        if date_start:
            domain.append(('date_start', '=', date_start))
        if date_stop:
            domain.append(('date_stop', '=', date_stop))
        if date_deadline:
            domain.append(('date_deadline', '=', date_deadline))
        if room_id:
            domain.append(('room_id', '=', room_id.id))
        if employee_id:
            domain.append(('employee_id', '=', employee_id.id))
        if type:
            domain.append(('type', '=', type))
        if priority:
            domain.append(('priority', '=', priority))
        if state:
            domain.append(('state', '=', state))
        if department_id:
            domain.append(('department_id', '=', department_id.id))

        hotel_work_order = self.env['hotel.work.order'].search(domain)

        for line in hotel_work_order:
            order_type = line.mapped('order_type')[0]
            date_start = line.mapped('date_start')[0]
            date_stop = line.mapped('date_stop')[0]
            date_deadline = line.mapped('date_deadline')[0]
            room_id = (line.mapped('room_id')).id
            employee_id = (line.mapped('employee_id')).id
            type = line.mapped('type')[0]
            priority = line.mapped('priority')[0]
            state = line.mapped('state')[0]
            department_id = (line.mapped('department_id')).id
            if line:
                self.env['work.order.line'].create({
                    'wizard_id': self.id,
                    'order_type': order_type,
                    'date_start': date_start,
                    'date_stop': date_stop,
                    'date_deadline': date_deadline,
                    'room_id': room_id,
                    'employee_id': employee_id,
                    'type': type,
                    'priority': priority,
                    'state': state,
                    'department_id': department_id,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'work.order',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_work_order_report').with_context(
            landscape=True).report_action(self)


class WorkOrderLine(models.TransientModel):
    _name = 'work.order.line'

    wizard_id = fields.Many2one('work.order')
    order_type = fields.Selection(selection=[('immediate', 'Immediate'), ('advance', 'Advance')])
    date_start = fields.Datetime()
    date_stop = fields.Datetime()
    date_deadline = fields.Datetime()
    room_id = fields.Many2one('hotel.room')
    employee_id = fields.Many2one('hr.employee')
    type = fields.Selection(selection=[
        ('fix', 'Fix'),
        ('maintenance', 'Maintenance'),
        ('clean', 'Clean'),
        ('other', 'Other'),
    ])
    priority = fields.Selection(selection=[
        ('high', 'High'),
        ('low', 'Low'),
        ('manual', 'Manual'),
    ])
    state = fields.Selection(selection=[
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('progress', 'Progress'),
        ('done', 'Done'),
    ])
    department_id = fields.Many2one('hr.department')
