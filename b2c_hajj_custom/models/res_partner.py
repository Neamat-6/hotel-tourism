from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import email_normalize
import requests
import logging
import base64
import qrcode
from io import BytesIO
import uuid
from odoo.osv import expression

logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    nationality_id = fields.Many2one('res.country', string="Nationality")
    residence_country_id = fields.Many2one('res.country', string="Country Of Residence")
    region = fields.Selection(string="Region", selection=[('sunni', 'Sunni'), ('shiite', 'Shiite'), ], required=False)
    language = fields.Many2one('res.lang', string="Language")
    pilgrim_type = fields.Selection(selection=[
        ('main', 'Main'), ('member', 'Family Member')
    ])
    main_member_id = fields.Many2one('res.partner')

    relationship = fields.Selection([
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('husband', 'Husband'),
        ('wife', 'Wife'),
    ], string="Relationship")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    tour_guide_id = fields.Many2one('res.partner', domain="[('is_guide', '=', True)]")
    passport_no = fields.Char(string='Passport Number')
    passport_expiry_date = fields.Date()
    package_id = fields.Many2one('booking.package')
    main_makkah = fields.Many2one('hotel.hotel', "Makkah Hotel", related='package_id.main_makkah', store=True)
    makkah_arrival_date = fields.Date("Makkah Arrival Date", related='package_id.makkah_arrival_date', store=True)
    makkah_departure_date = fields.Date("Makkah Departure Date", related='package_id.makkah_departure_date', store=True)
    makkah_room_type = fields.Selection(selection=[('2', '2'), ('3', '3'), ('4', '4')])

    main_madinah = fields.Many2one('hotel.hotel', "Madinah Hotel", related='package_id.main_madinah', store=True)
    madinah_arrival_date = fields.Date("Madinah Arrival Date", related='package_id.madinah_arrival_date', store=True)
    madinah_departure_date = fields.Date("Madinah Departure Date", related='package_id.madinah_departure_date',
                                         store=True)
    madinah_room_type = fields.Selection(selection=[('2', '2'), ('3', '3'), ('4', '4')])

    main_arfa = fields.Many2one('hotel.hotel', "Arfa Hotel", related='package_id.main_arfa', store=True)
    arfa_arrival_date = fields.Date("Arfa Arrival Date", related='package_id.arfa_arrival_date', store=True)
    arfa_departure_date = fields.Date("Arfa Departure Date", related='package_id.arfa_departure_date', store=True)

    main_minnah = fields.Many2one('hotel.hotel', "Minnah Hotel", related='package_id.main_minnah', store=True)
    minnah_arrival_date = fields.Date("Minnah Arrival Date", related='package_id.minnah_arrival_date', store=True)
    minnah_departure_date = fields.Date("Minnah Departure Date", related='package_id.minnah_departure_date', store=True)

    main_hotel = fields.Many2one('hotel.hotel', "Main Shift Hotel", related='package_id.main_hotel', store=True)
    hotel_arrival_date = fields.Date("Main Shift Arrival Date", related='package_id.hotel_arrival_date', store=True)
    hotel_departure_date = fields.Date("Main Shift Departure Date", related='package_id.hotel_departure_date',
                                       store=True)
    hotel_room_type = fields.Selection(selection=[('2', '2'), ('3', '3'), ('4', '4')])
    transportation_contract_ids = fields.Many2many('transportation.contract',
                                                    compute='_compute_transportation_contract_ids', store=True)
    flight_schedule_id = fields.Many2one('flight.schedule', "Flight Contract ID")
    flight_arrival_date = fields.Datetime("Arrival Date", related='flight_schedule_id.arrival_date', store=True)
    arrival_flight_no = fields.Char(related='flight_schedule_id.arrival_flight_no', string="Arrival Flight", store=True)
    departure_flight_no = fields.Char(related='flight_schedule_id.departure_flight_no', string="Departure Flight", store=True)
    arrival_airport_id = fields.Many2one(related='flight_schedule_id.arrival_airport_id', store=True)
    flight_departure_date = fields.Datetime("Departure Date", related='flight_schedule_id.departure_date', store=True)
    dep_airport_id = fields.Many2one(related='flight_schedule_id.departure_airport_id', store=True)
    is_guide = fields.Boolean("Is Guide")
    room_ref = fields.Char("Room Ref")
    portal_user_id = fields.Many2one('res.users')
    is_transportation_company = fields.Boolean("Is Transportation Company")
    flight_contract = fields.Char("Flight Contract")
    pilgrim_id = fields.Char("Pilgrim ID")
    ticket_number = fields.Char("Ticket Number")
    package_contract_id = fields.Many2one('package.contract')
    hajj_source = fields.Selection(selection=[('B2B', 'B2B'), ('B2C', 'B2C'), ('B2G', 'B2G')], string="Source")
    residence_country = fields.Char()
    nationality = fields.Char()
    visa_status = fields.Char(string='Visa Status')
    ticket_link = fields.Char(string='Ticket Link')
    booking_details = fields.Text(string='Booking Details')
    makkah_room = fields.Many2one('hotel.room', string="Makkah Room")
    madinah_room = fields.Many2one('hotel.room', string="Madinah Room")
    hotel_room = fields.Many2one('hotel.room', string="Hotel Room")
    arfa_room = fields.Many2one('hotel.room', string="Arfa Room")
    minnah_room = fields.Many2one('hotel.room', string="Minnah Room")
    status = fields.Selection([('in_source_country', 'في بلد القدوم'),
                               ('jaddah_air_arrival', 'مطار جده - وصول'),('jaddah_air_departure', 'مطار جده - مغادره'),
                               ('madinah_air_arrival', 'مطار المدينة -  وصول'), ('madinah_air_departure', 'مطار المدينة - للمغادرة'),
                               ('airport_makkah', 'الانتقال من المطار الي فندق مكة '),
                               ('madinah_airport', 'الانتقال الي المطار من فندق المدينة'), ('makah_airport', 'الانتقال الي المطار من فندق مكه'),
                               ('hotel_arfa', 'الانتقال من الفندق الي عرفة'), ('minnah_arrival', 'الوصول الي مني -تروية'),
                               ('minnah_arrival2', 'الوصول الي مني'), ('minnah_arfa', 'الانتقال من مني الى عرفة'),
                               ('arfa_arrival', 'الوصول الي عرفة'), ('arfa_mzdlfa', 'الانتقال من عرفة  الى مزدلفة'),
                               ('mzdlfa_minnah', 'الانتقال من مزدلفة الي مني'),('minnah_hotel', 'الانتقال من مني الي الفندق'),
                                 ('hotel_makkah_arrival', 'الوصول فندق مكه'), ('hotel_makkah_departure', 'المغادرة فندق مكه'),
                               ('hotel_madinah_arrival', 'الوصول فندق المدينة'), ('hotel_madinah_departure', 'المغادرة فندق المدينة')],
                              string="Status", default='in_source_country', tracking=True)

    is_hastened = fields.Boolean(string='متعجل', default=False)
    tarwiyah = fields.Boolean(string='تروية', default=False)
    ziarat_al_rawdah = fields.Boolean(string="زِيارَة الروضة", default=False)
    tawaf_al_qudum = fields.Boolean(string="طواف القدوم", default=False)
    jamarat_day1 = fields.Boolean(string="الجمرات اليوم الأول", default=False)
    jamarat_day2 = fields.Boolean(string="الجمرات اليوم الثاني", default=False)
    jamarat_day3 = fields.Boolean(string="الجمرات اليوم الثالث", default=False)
    jamarat_day4 = fields.Boolean(string="الجمرات اليوم الرابع", default=False)
    tawaf_al_ifada_sai = fields.Boolean(string="طواف الإفاضة والسعي", default=False)
    tawaf_al_wada = fields.Boolean(string="طواف الوداع", default=False)
    assistant_device_key = fields.Char("Assistant Device Key")
    assistant_device_id = fields.Char("Assistant Device Id")
    qr_code = fields.Binary("QR Code")
    x_qr_token = fields.Char(
        string="QR Token",
        readonly=True,
        copy=False,
        default=lambda self: str(uuid.uuid4())
    )
    saudi_mobile = fields.Char(string="Saudi Mobile")
    group_no = fields.Char(string="Group Number")
    
    makkah_actual_room_number = fields.Char(string="Makkah Actual Room Number")
    madinah_actual_room_number = fields.Char(string="Madinah Actual Room Number")
    minnah_actual_room_number = fields.Char(string="Minnah Actual Room Number")
    arfa_actual_room_number = fields.Char(string="Arfa Actual Room Number")
    minnah_sofa_number = fields.Char(string="Minnah Sofa Number")
    arfa_sofa_number = fields.Char(string="Arfa Sofa Number")
    upgraded = fields.Boolean(string="Upgraded")
    hotel_id = fields.Many2one('hotel.hotel', string="Hotel Category", help="Hotel category associated with this partner.")
    visa_contract_id = fields.Many2one('visa.contract')

    def generate_new_qr_code(self):
        for partner in self:
            # partner.x_qr_token = str(uuid.uuid4())
            if not partner.pilgrim_id:
                raise ValidationError(_("Please add Pilgrim ID to generate QR Code"))
            partner.generate_qr_code()

    def generate_qr_code(self):
        for partner in self:
            data = partner.pilgrim_id
            if not data:
                continue
            qr = qrcode.QRCode(box_size=4, border=2)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            partner.qr_code = base64.b64encode(buffer.getvalue())


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []

        domain = []
        if name:
            print('called name_search',name)
            domain = expression.OR([
                [('name', operator, name)],
                [('pilgrim_id', operator, name)],
                [('mobile', operator, name)],
                [('email', operator, name)],
            ])
        print('domain',domain)
        return self.search(expression.AND([domain, args]), limit=limit).name_get()

    @api.depends('package_id.transportation_contract_ids')
    def _compute_transportation_contract_ids(self):
        for rec in self:
            rec.transportation_contract_ids = rec.package_id.transportation_contract_ids

    @api.onchange('flight_contract')
    @api.constrains('flight_contract')
    def get_flights_info(self):
        for record in self:
            if record.flight_contract:
                flight_schedule_obj = self.env['flight.schedule'].sudo().search(
                    [('name', 'ilike', record.flight_contract)], limit=1)
                if not flight_schedule_obj:
                    flight_schedule_obj = self.env['flight.schedule'].sudo().create({
                        'name': record.flight_contract,
                        'pilgrims_no': 1,
                    })
                record.flight_schedule_id = flight_schedule_obj.id

    @api.onchange('pilgrim_type')
    def onchange_pilgrim_type(self):
        self.main_member_id = False

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        print('called partner create',vals)
        if vals.get('package_id', False):
            res.assign_to_bookings()
        res.generate_qr_code()
        return res

    def write(self, vals):
        if self.env.context.get('skip_assign_to_bookings'):
            return super(Partner, self).write(vals)
        for rec in self:
            print('called partner write', vals)
            old_package = rec.package_id  # Save old value before write
            res = super(Partner, rec).write(vals)

            # Fields that trigger re-assignment
            fields = [
                'package_id', 'makkah_room_type', 'madinah_room_type', 'hotel_room_type',
                'gender', 'main_member_id', 'pilgrim_type', 'name', 'email', 'street',
                'mobile', 'country_id', 'state_id', 'city', 'zip', 'nationality_id',
                'region', 'language', 'relationship'
            ]

            # Only call assign_to_bookings if any of these fields changed
            if any(field in vals for field in fields):
                print('go to sassign to booking')
                rec.with_context(skip_assign_to_bookings=True).assign_to_bookings(
                    old_package=old_package
                )
        return True

    def unlink(self):
        """ Remove the partner from guest lists and allowed beds before deletion. """
        for partner in self:
            partner.remove_from_bookings()
        return super(Partner, self).unlink()

    def create_portal_user(self):
        if not self.email:
            raise ValidationError("Please add an email address before creating a portal user.")

        user_sudo = self.env['res.users'].search([('partner_id', '=', self.id)], limit=1).sudo()
        if not user_sudo:
            company = self.company_id or self.env.company
            user_sudo = self.sudo().with_company(company.id)._create_user()
            group_portal = self.env.ref('base.group_portal')
            group_tax   = self.env.ref('account.group_show_line_subtotals_tax_excluded')
            user_sudo.write({'groups_id': [(6, 0, [group_portal.id, group_tax.id])]})
            self.portal_user_id = user_sudo.id

        user_sudo.partner_id.signup_prepare()
        self.generate_ai_device()
        self.add_meta_data_to_assistant_device()
        self.with_context(active_test=True)._send_email()

    def generate_ai_device(self):
        for rec in self:
            if not rec.pilgrim_id:
                raise ValidationError("Please set a Pilgrim ID on this partner before registering with EntaAI.")
            login_url = 'https://entaai.net:8080/api/login'
            login_payload = {
                "email":    "admin@example.com",
                "password": "password123",
            }
            try:
                res = requests.post(login_url, json=login_payload, timeout=10)
                res.raise_for_status()
                admin_token = res.json().get('auth_token')
                if not admin_token:
                    raise UserError("No auth_token returned from EntaAI /api/login")
            except Exception as e:
                raise UserError(f"Failed to authenticate to EntaAI API: {e}")

            store_url = 'https://entaai.net:8080/api/admin/devices/store'
            device_payload = {
                "name":                rec.pilgrim_id,
                "manager_name":        "manager name",
                "manager_email":       "mg@mail.com",
                "manager_phone":       "6516525",
                "subscription_status": "active",
                "assistant_id":        31,
                "start_date":          "2025-04-22",
                "end_date":            "2025-05-22",
                "customer_id":         3,
            }
            headers = {
                "Authorization": f"{admin_token}",
            }
            try:
                res2 = requests.post(store_url, json=device_payload, headers=headers, timeout=10)
                res2.raise_for_status()
                device_token = res2.json().get('auth_token')
                device_id = res2.json().get('id')
                if not device_token:
                    raise UserError("No auth_token returned from EntaAI /api/admin/devices/store")
                rec.assistant_device_key = device_token
                rec.assistant_device_id = device_id
            except Exception as e:
                raise UserError(f"Failed to register device with EntaAI API: {e}")
            
            
    def add_meta_data_to_assistant_device(self):
        for rec in self:
            if not rec.assistant_device_id:
                raise ValidationError(_("Cannot add metadata: assistant_device_id is not set."))

            login_url = 'https://entaai.net:8080/api/login'
            login_payload = {
                "email":    "admin@example.com",
                "password": "password123",
            }
            try:
                login_res = requests.post(login_url, json=login_payload, timeout=10)
                login_res.raise_for_status()
                admin_token = login_res.json().get('auth_token')
                if not admin_token:
                    raise UserError(_("No auth_token returned from EntaAI /api/login"))
            except Exception as e:
                raise UserError(_("Failed to authenticate to EntaAI API: %s") % e)

            headers = {
                "Authorization": admin_token,
            }
            device_id = rec.assistant_device_id
            base_meta_url = f'https://entaai.net:8080/api/core/devices/{device_id}/meta/item'

            metas = {
                "Makkah Hotel":      rec.main_makkah.name if rec.main_makkah else '',
                "Madinah Hotel":     rec.main_madinah.name if rec.main_madinah else '',
                "Arafa Hotel":       rec.main_arfa.name if rec.main_arfa else '',
                "Minnah Hotel":      rec.main_minnah.name if rec.main_minnah else '',

                "Makkah Arrival Date":   (rec.makkah_arrival_date and rec.makkah_arrival_date.isoformat()) or '',
                "Madinah Arrival Date":  (rec.madinah_arrival_date and rec.madinah_arrival_date.isoformat()) or '',
                "Arfa Arrival Date":     (rec.arfa_arrival_date and rec.arfa_arrival_date.isoformat()) or '',
                "Minnah Arrival Date":   (rec.minnah_arrival_date and rec.minnah_arrival_date.isoformat()) or '',

                "Makkah Departure Date":   (rec.makkah_departure_date and rec.makkah_departure_date.isoformat()) or '',
                "Madinah Departure Date":  (rec.madinah_departure_date and rec.madinah_departure_date.isoformat()) or '',
                "Arfa Departure Date":     (rec.arfa_departure_date and rec.arfa_departure_date.isoformat()) or '',
                "Minnah Departure Date":   (rec.minnah_departure_date and rec.minnah_departure_date.isoformat()) or '',

                "Makkah Actual Room Number":   rec.makkah_actual_room_number or '',
                "Madinah Actual Room Number":  rec.madinah_actual_room_number or '',
                "Arfa Actual Room Number":     rec.arfa_actual_room_number or '',
                "Minnah Actual Room Number":   rec.minnah_actual_room_number or '',
            }

            for key, value in metas.items():
                payload = {"key": key, "value": value}
                try:
                    meta_res = requests.post(base_meta_url, json=payload, headers=headers, timeout=10)
                    meta_res.raise_for_status()
                except Exception as e:
                    raise UserError(_(
                        "Failed to save meta item '%s' → '%s':\n%s"
                    ) % (key, value, e))

        

    def _create_user(self):

        return self.env['res.users'].with_context(no_reset_password=True)._create_user_from_template({
            'email': email_normalize(self.email),
            'login': email_normalize(self.email),
            'partner_id': self.id,
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, self.env.company.ids)],
            'active': True,
        })

    def _send_email(self):
        self.ensure_one()
        template = self.env.ref('b2c_hajj_custom.mail_template_data_portal_welcome')
        if not template:
            raise UserError(_('The template "Portal: new user" not found for sending email to the portal user.'))

        lang = self.sudo().lang
        partner = self.sudo()

        portal_url = partner.with_context(signup_force_type_in_url='', lang=lang)._get_signup_url_for_action()[
            partner.id]
        partner.signup_prepare()

        template.with_context(dbname=self._cr.dbname, portal_url=portal_url, lang=lang).send_mail(self.id,
                                                                                                  force_send=True)
        return True

    def send_whatsapp_message(self):
        print('called send_whatsapp_message')
        link = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        company = self.env['res.company'].sudo().search([], order='id asc', limit=1)
        company_name = company.name
        wizard_vals = {
            'partner_ids': self.id,
            'message': (
        f"السلام عليكم ورحمة الله وبركاته،\n\n"
        f"عميلنا الكريم،\n"
        f"نحيطكم علمًا بأنه تم إرسال رسالة جديدة لكم عبر بوابة الخدمات الخاصة بالحجاج التابعة لـ {company_name}.\n"
        f"نرجو منكم التفضل بالدخول إلى البوابة للاطلاع على تفاصيل الرسالة واتخاذ اللازم.\n\n"
        f"رابط الدخول إلى بوابة الخدمات:\n"
        f"{link}\n\n"
        f"نسعد بخدمتكم،\n"
        f"فريق عمل {company_name}\n\n"
        "----------------------------------------\n\n"
        f"Dear Valued Pilgrim,\n\n"
        f"We would like to inform you that a new message has been sent to you via the Pilgrim Services Portal of {company_name}.\n"
        f"Please log in to the portal to view the message details and take any necessary action.\n\n"
        f"Access the services portal through the following link:\n"
        f"{link}\n\n"
        f"We are always pleased to serve you.\n"
        f"{company_name} Team"
    ),
        }
        wizard = self.env['sh.send.whatsapp.message.wizard'].create(wizard_vals)
        wizard.action_send_whatsapp_message()


    def create_chat_channel_with(self, admin_partner):
        """Creates a private chat channel with another partner."""
        self.ensure_one()
        try:
            self.send_whatsapp_message()
        except Exception as e:
            logger.info(f'can not send whatsapp message: {e}')

        channel = self.env['mail.channel'].sudo().search([
            ('channel_partner_ids', 'in', [self.id]),
            ('channel_partner_ids', 'in', [admin_partner.id]),
            ('channel_type', '=', 'chat'),
        ], limit=1)

        if not channel:
            channel = self.env['mail.channel'].sudo().create({
                'name': f'Booking Chat - {self.name}',
                'channel_type': 'chat',
                'channel_partner_ids': [(4, self.id)],
            })
            channel.sudo().write({
                'channel_partner_ids': [(4, admin_partner.id)]
            })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/mail/view?channel_id={channel.id}',
            'target': 'self',
        }

    def create_admin_chat(self):
        # admin_partner = self.env.ref('base.user_admin').partner_id
        admin_partner = self.env.user.partner_id
        print('admin_partner', admin_partner)
        return self.create_chat_channel_with(admin_partner)

    def action_send_pilgrim_barcode_whatsapp(self):
        self.ensure_one()

        # Render PDF report
        report = self.env.ref('b2c_hajj_custom.action_pilgrim_barcode')
        pdf_content, content_type = report._render_qweb_pdf(self.ids)

        message = """
        🇸🇦 العربية:
        مرحبًا بكم في مكة المكرمة، وتتمنى لكم شركة دور للضيافة حجًا مبرورًا وسعيًا مشكورًا.
        يسعدنا أن نرافقكم خلال رحلتكم المباركة، وهذا الرقم هو رقم الدعم المباشر. لا تترددوا في التواصل معنا لأي استفسار أو مساعدة على مدار الساعة.
        نسأل الله أن يتقبل طاعتكم وييسر أموركم.

        ⸻

        🇬🇧 English:
        Welcome to Makkah! Dor Hospitality warmly wishes you an accepted Hajj and a blessed journey.
        This number is our live support line. Feel free to contact us anytime for inquiries or assistance throughout your stay.
        May your pilgrimage be easy and accepted.

        ⸻

        🇫🇷 Français :
        Bienvenue à La Mecque ! Dor Hospitality vous souhaite un Hajj accepté et une expérience bénie.
        Ce numéro est notre ligne d’assistance en direct. N’hésitez pas à nous contacter à tout moment pour toute question ou aide.
        Que votre pèlerinage soit facilité et accepté.

        ⸻

        🇩🇪 Deutsch:
        Willkommen in Mekka! Dor Hospitality wünscht Ihnen eine gesegnete und angenommene Hadsch-Reise.
        Diese Nummer ist unsere Live-Support-Hotline. Zögern Sie nicht, uns jederzeit bei Fragen oder Anliegen zu kontaktieren.
        Möge Ihre Pilgerfahrt angenommen und gesegnet sein.
        """

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}_QrCode.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'res.partner',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        # Prepare wizard values
        wizard_vals = {
            'message': message,
            'attachment_ids': [(6, 0, [attachment.id])],
            'partner_ids': self.id,
        }

        # Create and run wizard
        context = dict(self.env.context)
        context.update({'active_ids': [self.id], 'active_model': 'res.partner'})
        wizard = self.with_context(context).env['sh.send.whatsapp.message.wizard'].create(
            wizard_vals)
        wizard.action_send_whatsapp_message()

    def assign_to_bookings(self, old_package=None):
        """ Assign partner to bookings, removing from the old package if changed. """
        print('callled assign_to_bookings', self, old_package)
        for record in self:
            if record.id not in record.package_id.message_partner_ids.ids:
                record.package_id.message_subscribe(partner_ids=[record.id])
            bookings = self.env['hotel.booking'].sudo().search(
                [('package_id', '=', record.package_id.id)])
            if old_package and old_package != record.package_id:
                if record.id in old_package.message_partner_ids.ids:
                    old_package.message_unsubscribe(partner_ids=[record.id])
                print('first stage', old_package, record.package_id)
                # Remove the partner from the previous package's bookings
                old_bookings = self.env['hotel.booking'].sudo().search(
                    [('package_id', '=', old_package.id)])
                for old_booking in old_bookings:
                    remove_guest_line = old_booking.guest_ids.filtered(lambda g: g.partner_id == self)
                    if remove_guest_line.folio_id:
                        remove_guest_line.folio_id.bed_ids.filtered(lambda b: b.partner_id == self).write({'partner_id': False})
                    print('remove_guest_line', remove_guest_line)
                    remove_guest_line.unlink()
                    for bed in old_booking.folio_ids.mapped('bed_ids'):
                        bed.allowed_partner_ids = bed.allowed_partner_ids.filtered(lambda p: p != self)

            if not record.package_id or not bookings:
                return  # If package_id is removed, stop further execution

            print('called assign_to_bookings', bookings)
            for booking in bookings:
                print('booking', booking)
                booked_room_type = False
                if booking.hotel_id.type == 'makkah' and record.makkah_room_type:
                    booked_room_type = record.makkah_room_type
                elif booking.hotel_id.type == 'madinah' and record.madinah_room_type:
                    booked_room_type = record.madinah_room_type
                elif booking.hotel_id.type == 'hotel' and record.hotel_room_type:
                    booked_room_type = record.hotel_room_type

                # Check if guest already exists
                existing_guest = booking.guest_ids.filtered(lambda g: g.partner_id == record)
                print('existing_guest', existing_guest)
                if existing_guest:
                    # Update the existing guest instead of creating a new one
                    if existing_guest.folio_id and ((
                            booked_room_type != existing_guest.booked_room_type) or (
                            existing_guest.gender != record.gender) or (
                            existing_guest.main_member_id != record.main_member_id)):
                        existing_guest.folio_id.bed_ids.filtered(lambda b: b.partner_id == record).write({'partner_id': False})
                        existing_guest.write({'folio_id': False})
                    existing_guest.write({
                        'guest_name': record.name,
                        'guest_email': record.email,
                        'guest_address': record.street,
                        'guest_mobile': record.mobile,
                        'guest_country_id': record.country_id.id,
                        'guest_state_id': record.state_id.id,
                        'guest_city': record.city,
                        'guest_zip_code': record.zip,
                        'nationality_id': record.nationality_id.id,
                        'region': record.region,
                        'language': record.language.id,
                        'relationship': record.relationship,
                        'gender': record.gender,
                        'main_member_id': record.main_member_id.id,
                        'pilgrim_type': record.pilgrim_type,
                        'booked_room_type': booked_room_type,
                    })
                else:
                    # Add new guest if not already in guest_ids
                    print('new guest')
                    booking.write({
                        'guest_list': True,
                        'guest_ids': [(0, 0, {
                            'partner_id': record.id,
                            'guest_name': record.name,
                            'guest_email': record.email,
                            'guest_address': record.street,
                            'guest_mobile': record.mobile,
                            'guest_country_id': record.country_id.id,
                            'guest_state_id': record.state_id.id,
                            'guest_city': record.city,
                            'guest_zip_code': record.zip,
                            'nationality_id': record.nationality_id.id,
                            'region': record.region,
                            'language': record.language.id,
                            'relationship': record.relationship,
                            'gender': record.gender,
                            'main_member_id': record.main_member_id.id,
                            'pilgrim_type': record.pilgrim_type,
                            'booked_room_type': booked_room_type,
                        })]
                    })

                # Assign partner to allowed beds if not already assigned
                for bed in booking.folio_ids.mapped('bed_ids'):
                    if record not in bed.allowed_partner_ids:
                        bed.allowed_partner_ids = [(4, record.id)]

    def remove_from_bookings(self):
        """ Remove partner from all bookings and allowed beds (when deleting). """
        for booking in self.env['hotel.booking'].sudo().search([('guest_ids.partner_id', '=', self.id)]):
            booking.guest_ids = booking.guest_ids.filtered(lambda g: g.partner_id != self)
            for bed in booking.folio_ids.mapped('bed_ids'):
                bed.allowed_partner_ids = bed.allowed_partner_ids.filtered(lambda p: p != self)

    def in_source_country(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'in_source_country'})

    def jaddah_air_arrival(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'jaddah_air_arrival'})

    def jaddah_air_departure(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'jaddah_air_departure'})

    def madinah_air_arrival(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'madinah_air_arrival'})

    def madinah_air_departure(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'madinah_air_departure'})

    def airport_makkah(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'airport_makkah'})


    def madinah_airport(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'madinah_airport'})

    def makah_airport(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'makah_airport'})

    def hotel_arfa(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'hotel_arfa'})

    def minnah_arrival(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'minnah_arrival'})

    def minnah_arrival2(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'minnah_arrival2'})

    def minnah_arfa(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'minnah_arfa'})

    def arfa_arrival(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'arfa_arrival'})

    def arfa_mzdlfa(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'arfa_mzdlfa'})

    def mzdlfa_minnah(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'mzdlfa_minnah'})

    def minnah_hotel(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'minnah_hotel'})

    def hotel_makkah_arrival(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'hotel_makkah_arrival'})

    def hotel_makkah_departure(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'hotel_makkah_departure'})

    def hotel_madinah_arrival(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'hotel_madinah_arrival'})

    def hotel_madinah_departure(self):
        for rec in self:
            rec.sudo().with_context(skip_assign_to_bookings=True).write({'status': 'hotel_madinah_departure'})
