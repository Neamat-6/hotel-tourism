{
    'name': "User Audit Log",
    'summary': """  """,
    'author': "Ahmed Elgamal",
    'version': '15.0.0.0',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/user_audit_log_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
