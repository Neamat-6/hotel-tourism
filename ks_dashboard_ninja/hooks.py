
from odoo.api import Environment, SUPERUSER_ID

def auto_import_dashboard(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    env['ks_dashboard_ninja.import'].auto_import_dashboard_json()