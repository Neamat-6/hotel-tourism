from odoo import fields, models, api, _
import requests
from datetime import timedelta
from datetime import datetime
import pytz
import logging
from firebase_admin import messaging
logger = logging.getLogger(__name__)


class GuestOrder(models.Model):
    _name = 'guest.order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Hotel Guest Order'
    _order = 'date_order desc, id desc'
    _check_company_auto = True


    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Guest', index=True, tracking=1, domain=lambda self: self._get_checked_in_partners_domain())
    order_line = fields.One2many('guest.order.line', 'order_id', string='Order Lines')
    state = fields.Selection([
        ('draft', 'New'),
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('late', 'Late')
    ], default='draft', string="Status", tracking=True)
    date_order = fields.Datetime(string='Estimated Start Time', default=fields.Datetime.now, readonly=True)
    end_date_order = fields.Datetime(string='Estimated End Time', compute='_compute_end_date_order', store=True)
    actual_start_time = fields.Datetime(string='Actual Start Time', compute='_compute_actual_time', store=True)
    actual_end_time = fields.Datetime(string='Actual End Time', compute='_compute_actual_time', store=True)
    paid_status = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid')], string='Paid Status', default='unpaid')
    user_id = fields.Many2one('res.users', string='Employee', index=True, tracking=2,
                                domain="[('categ_ids','=', categ_id), "
                                       "('company_ids', '=', company_id), "
                                       "('groups_id', '=', group_id), "
                                       "('groups_id', 'not in', groups_ids)]")
    note = fields.Text()
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, compute='_amount_all', tracking=5)
    amount_tax = fields.Monetary(string='Taxes', store=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, compute='_amount_all', tracking=4)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id.id,
                                  required=True, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    categ_id = fields.Many2one('product.category', string='Category', required=True)
    group_id = fields.Many2one('res.groups', string="Group",
                               default=lambda self: self._get_default_group())
    groups_ids = fields.Many2many('res.groups', string="Groups", default=lambda self: self._get_default_groups())

    @api.model
    def _get_default_group(self):
        # You can specify logic here to determine the default value for the M2O field
        return self.env.ref('hotel_guest_order.group_guest_order_user')  # Example: default to "User" group

    @api.model
    def _get_default_groups(self):
        # Specify logic to get the default groups for the M2M field
        group_1 = self.env.ref('hotel_guest_order.group_guest_order_admin')  # Example: User group
        group_2 = self.env.ref('hotel_guest_order.group_guest_order_superadmin')  # Example: ERP Manager group

        # Return both groups in a recordset for Many2many field
        return self.env['res.groups'].browse([group_1.id, group_2.id])

    def _get_checked_in_partners_domain(self):
        booking = self.env['booking.folio'].search(
            [('state', '=', 'checked_in'), ('company_id', '=', self.company_id.id or self.env.company.id)])
        partner_ids = booking.mapped('partner_id').mapped('id')
        print('partner_ids', partner_ids)
        return [('id', 'in', partner_ids)]

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.depends('date_order', 'order_line.period')
    def _compute_end_date_order(self):
        """
        Compute the end date of the order.
        """
        for order in self:
            if order.date_order and order.order_line:
                period = sum(line.period for line in order.order_line)
                order.end_date_order = order.date_order + timedelta(minutes=period)
            else:
                order.end_date_order = False


    @api.onchange('categ_id', 'company_id')
    def _onchange_categ_id(self):
        for rec in self:
            rec.user_id = False
            rec.order_line = [(6, 0, [])]

    def action_pending(self):
        """
        Set the order status to pending.
        """
        for order in self:
            order.state = 'pending'

    def action_done(self):
        """
        Set the order status to done.
        """
        for order in self:
            order.state = 'done'

    def action_late(self):
        """
        Set the order status to late.
        """
        for order in self:
            order.state = 'late'

    @api.depends('state')
    def _compute_actual_time(self):
        for order in self:
            order.actual_start_time = False
            order.actual_end_time = False
            if order.state == 'pending':
                order.actual_start_time = fields.Datetime.now()
            elif order.state == 'done':
                order.actual_end_time = fields.Datetime.now()

    @api.model
    def mark_late_orders(self):
        now = fields.Datetime.now()
        orders = self.search([
            ('end_date_order', '<=', now),
            ('state', 'not in', ['done', 'late']),
        ])
        for order in orders:
            order.state = 'late'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('guest.order') or _('New')
        if not vals.get('user_id') and vals.get('categ_id'):
            matching_user = self._find_best_matching_user(vals['categ_id'], vals.get('company_id'))
            if matching_user:
                vals['user_id'] = matching_user.id
        result = super().create(vals)
        result.get_users_to_notify()
        return result


    def write(self, vals):
        if 'categ_id' in vals and not vals.get('user_id'):
                matching_user = self._find_best_matching_user(vals['categ_id'])
                if matching_user:
                    vals['user_id'] = matching_user.id
        result = super().write(vals)
        if vals.get('user_id'):
            self.get_users_to_notify(update=True)
        return result

    def _find_best_matching_user(self, categ_id, company_id=None):
        # Find users having categ_id
        group_user = self.env.ref('hotel_guest_order.group_guest_order_user')
        users = self.env['res.users'].search([
            ('categ_ids', '=', categ_id),
            ('company_ids', '=', company_id or self.company_id.id),
        ])
        if not users:
            return False

        # For each user, count pending guest orders
        user_pending_count = {}
        users = users.filtered(lambda u: group_user in u.groups_id and not u.has_group(
            'hotel_guest_order.group_guest_order_admin') and not u.has_group('hotel_guest_order.group_guest_order_superadmin'))
        for user in users:
            count = self.env['guest.order'].search_count([
                ('user_id', '=', user.id),
                ('state', 'in', ['draft', 'pending'])  # assuming draft means pending
            ])
            user_pending_count[user] = count

        # Find the user with minimum pending orders
        best_user = min(user_pending_count, key=user_pending_count.get, default=False)
        return best_user

    def get_users_to_notify(self, update=False):
        logger.info(f'get_users_to_notify with update={update}')
        for order in self:
            if order.user_id:
                if order.user_id.device_token:
                    self.send_firebase_notification(
                    device_token=order.user_id.device_token,
                    title=f'New Order {order.name}',
                    body='You have a new order in Odoo.'
                    )

            if order.categ_id and not update:
                group_1 = self.env.ref('hotel_guest_order.group_guest_order_admin').id
                group_2 = self.env.ref('hotel_guest_order.group_guest_order_superadmin').id
                super_users = self.env['res.users'].search([
                    ('categ_ids', '=', order.categ_id.id),
                    ('company_ids', '=', order.company_id.id),
                    ('groups_id', '=', group_1),
                    ('groups_id', '!=', group_2),
                ])
                logger.info(f'super_users={super_users}')
                for user in super_users:
                    if user.device_token:
                        self.send_firebase_notification(
                            device_token=user.device_token,
                            title=f'New Order {order.name}',
                            body='New Order has been created.'
                        )

    def send_firebase_notification(self, device_token, title, body):
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                token=device_token,
            )
            response = messaging.send(message)
            logger.info(f"Notification sent: {response}")
            return {'status': 'success', 'response': response}
        except Exception as e:
            logger.error(f"Failed to send FCM notification: {e}")
            return {'status': 'error', 'message': str(e)}


class GuestOrderLine(models.Model):
    _name = 'guest.order.line'
    _description = 'Hotel Guest Order Line'
    _order = 'order_id, id'
    _check_company_auto = True


    name = fields.Char(string='Description')
    order_id = fields.Many2one('guest.order', string='Order Reference')
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        change_default=True, ondelete='restrict', check_company=True)
    categ_id = fields.Many2one('product.category', string='Category', related='order_id.categ_id', store=True)
    period = fields.Integer(string='Period Per Minutes', related='product_id.period')
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure',
                                   required=True, default=1.0)
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]",
                              context={'active_test': False})
    location = fields.Char(string='Location')
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True,
                                 index=True)
    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Salesperson')
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'],
                                  store=True, string='Currency')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    available_product_ids = fields.Many2many(
    'product.product',
    compute='_compute_available_products',
    string="Available Products",)

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.product_uom_qty * line.price_unit

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })


    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Onchange method for product_id field.
        """
        for line in self:
            if line.product_id:
                line.name = line.product_id.display_name
                line.price_unit = line.product_id.lst_price
                line.tax_id = line.product_id.taxes_id.filtered(lambda t: t.company_id == line.company_id)

    # @api.onchange('categ_id')
    # def _onchange_product_id_filter_by_available_hours(self):
    #     for line in self:
    #         line.product_id = False
    #         print('callled change product')
    #         if not line.order_id or not line.order_id.date_order:
    #             return
    #         user_tz = self.env.user.tz or 'UTC'
    #         order_dt = line.order_id.date_order  # This is in UTC
    #
    #         # Convert to user's local timezone
    #         print('user', self.env.user)
    #         print('order_dt', order_dt)
    #         print('user_tz', user_tz)
    #         user_timezone = pytz.timezone(user_tz)
    #         print('user_timezone', user_timezone)
    #         local_dt = order_dt.astimezone(user_timezone)
    #         print('local_dt', local_dt)
    #         current_hour = local_dt.hour + local_dt.minute / 60.0
    #         print('current_hour', current_hour)
    #         # Build domain to restrict product selection
    #         domain = [('sale_ok', '=', True),
    #                   '|', ('company_id', '=', False), ('company_id', '=', line.company_id.id),
    #                   ('from_hour', '<=', current_hour),
    #                   ('to_hour', '>=', current_hour),
    #                   ('categ_id', '=', line.categ_id.id),
    #                   ]
    #         print('domain', domain)
    #         return {
    #             'domain': {
    #                 'product_id': domain
    #             }
    #         }

    @api.depends('order_id.date_order', 'categ_id')
    def _compute_available_products(self):
        for line in self:
            if not line.order_id or not line.order_id.date_order:
                line.available_product_ids = self.env['product.product']
                continue

            user_tz = self.env.user.tz or 'UTC'
            user_timezone = pytz.timezone(user_tz)
            local_dt = line.order_id.date_order.astimezone(user_timezone)
            current_hour = local_dt.hour + local_dt.minute / 60.0

            domain = [
                ('from_hour', '<=', current_hour),
                ('to_hour', '>=', current_hour)
            ]
            if line.categ_id:
                domain.append(('categ_id', '=', line.categ_id.id))
            line.available_product_ids = self.env['product.product'].search(domain)



