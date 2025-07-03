from odoo import fields, models, api
import logging
logger = logging.getLogger(__name__)


class BookingLine(models.Model):
    _inherit = 'hotel.booking.line'

    ezee_transaction_id = fields.Char()

    def get_price_unit(self, booking_line, day):
        logger.info('get_price_unit ezee')
        price_unit = super(BookingLine, self).get_price_unit(booking_line, day)
        if booking_line.booking_id.ezee_apply_daily_price:
            logger.info('get_price_unit ezee ezee_apply_daily_price')
            price_unit = booking_line.rate_plan.sudo().rock_rate
            price_id = booking_line.booking_id.daily_price_ids.filtered(
                lambda
                    p: p.date == day and p.room_type_id.id == booking_line.room_type.id and p.rate_plan_id.id == booking_line.rate_plan.id
            )
            logger.info(f'get_price_unit ezee {price_unit}-- {price_id}')
            if price_id:
                price_id = price_id[0]
                price_id.booking_line_id = booking_line.id
                price_unit = price_id.price
        logger.info(f'get_price_unit ezee price_unit {price_unit}')
        return price_unit

    def update_folio(self, number_of_rooms, price=False, room_type=False,check_in=False,check_out=False):
        res = super(BookingLine, self).update_folio(number_of_rooms, price=price, room_type=room_type,check_in=check_in,check_out=check_out)
        if self.hotel_id.enable_ezee and self.folio_ids and self.booking_id.ezee_apply_daily_price:
            wizard = self.env['ezee.connector'].create({
                'date_from': self.booking_id.check_in_date,
                'date_to': self.booking_id.check_out_date,
                'action_type': 'update_inventory',
                'company_id': self.company_id.id,
                'room_type_ids': [(6, 0, [self.room_type.id])],
            })
            wizard.button_search()
            wizard.button_update_inventory()
            self.env['audit.trails'].create({
                'booking_id': self.booking_id.id,
                'user_id': self.env.user.id,
                'operation': 'ezee',
                'datetime': fields.Datetime.now(),
                'notes': wizard.note
            })
        return res
