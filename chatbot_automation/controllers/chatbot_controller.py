import json
from odoo import http
from odoo.http import request
from werkzeug.exceptions import Unauthorized, BadRequest

class ChatbotController(http.Controller):
    @http.route(
        '/chatbot/execute_tour',
        type='json',
        auth='public',    
        csrf=False,       
        methods=['POST']
    )
    def execute_tour(self, **payload):
        auth = request.httprequest.authorization
        if not auth or auth.type.lower() != 'basic':
            raise Unauthorized("Missing or invalid Authorization header")

        username, password = auth.username, auth.password

        try:
            request.session.authenticate(request.db, username, password)
        except Exception:
            raise Unauthorized("Invalid username/password")

        user = request.env.user
        steps = payload.get('steps') or []

        Tour = request.env['chatbot.tour'].sudo()

        Tour.search([('user_id', '=', user.id)]).unlink()
        Tour.create({
            'user_id':   user.id,
            'steps':     json.dumps(steps),
            'processed': False,
        })

        return {'status': 'ok'}

    @http.route(
        '/chatbot/get_tour',
        type='http',
        auth='user',
        csrf=False,
        methods=['GET'],
    )
    def get_tour(self, **kw):
        auth = request.httprequest.authorization
        if not auth or auth.type.lower() != 'basic':
            raise Unauthorized("Missing or invalid Authorization header")
        try:
            request.session.authenticate(request.db, auth.username, auth.password)
        except Exception:
            raise Unauthorized("Invalid username/password")

        rec = request.env['chatbot.tour'].sudo().search([
            ('user_id', '=', request.env.user.id),
            ('processed', '=', False),
        ], limit=1)

        steps = []
        if rec:
            rec.processed = True
            try:
                steps = json.loads(rec.steps or '[]')
            except json.JSONDecodeError:
                steps = []

        headers = [('Content-Type', 'application/json')]
        return request.make_response(json.dumps({'steps': steps}), headers=headers)