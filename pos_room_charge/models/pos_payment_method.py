from odoo import models, fields, api


class PosPaymentMethod(models.Model):
  _inherit = 'pos.payment.method'

  use_for_room_charge = fields.Boolean(
      'Use for Room Charge',
      default=False,
  )
