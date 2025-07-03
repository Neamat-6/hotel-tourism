from odoo import models, fields

class ChatbotTour(models.Model):
    _name = 'chatbot.tour'
    _description = 'Chatbot UI Tour Queue'

    user_id     = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    steps       = fields.Text(string="Tour Steps", default='[]')  # Default to empty JSON array
    processed   = fields.Boolean(string="Has Been Processed", default=False)
    create_date = fields.Datetime(string="Created On", default=fields.Datetime.now)