{
    'name': "Access Right Template User",
    'summary': """  """,
    'author': "Ahmed Elgamal",
    'version': '15.0.0.0',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_user_view.xml',
        'views/user_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
