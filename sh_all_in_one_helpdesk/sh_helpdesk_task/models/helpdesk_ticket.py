# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields,api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    task_count = fields.Integer('Tasks', compute='_compute_task_count')
    task_ids = fields.Many2many('project.task', string='Task')

    def _compute_task_count(self):
        if self:
            for rec in self:
                rec.task_count = 0
                task_ids = self.env['project.task'].sudo().search(
                    [('sh_ticket_ids', 'in', [rec.id])])
                if task_ids:
                    rec.task_count = len(task_ids.ids)

    def create_task(self):
        return{
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_name': self.name,
                'default_user_id': self.user_id.id,
                'default_sh_ticket_ids': [(4, self.id)],
                'default_partner_id': self.partner_id.id,
                'default_date_deadline': fields.Date.today(),
                'default_description': self.description
            }
        }

    def view_task(self):
        task_ids = self.env['project.task'].sudo().search(
            [('sh_ticket_ids', 'in', [self.id])])
        return{
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_mode': 'kanban,tree,form',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', task_ids.ids)],
            'target': 'current',
        }

  
    @api.model
    def default_get(self, fields_list):
        res = super(HelpdeskTicket, self).default_get(fields_list)
        if self.env.context:
            partner=self.env['res.partner'].sudo().browse(self.env.context.get('partner_id'))
            res.update({
                'partner_id':partner.id if partner else False,
                'person_name': partner.name if partner else '',
                'email':partner.email if partner else False,
                'task_ids':[(4,self.env.context.get('task_id'))] if self.env.context.get('task_id') else False,
                'description':self.env.context.get('description') if self.env.context.get('description') else '',
                'user_id':self.env.context.get('user_ids')[0] if self.env.context.get('user_ids') else False,
            })
            if self.env.context.get('user_ids') and len(self.env.context.get('user_ids'))>1:
                sh_users=[]
                for user in self.env.context.get('user_ids')[1:]:
                    sh_users.append((4,user))
                res.update({
                    'sh_user_ids' : sh_users,
                })
   
        return res