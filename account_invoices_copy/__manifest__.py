{
    'name': "Account Invoice Copy",
    'summary': """
        The module adds the ability to copy vendor accounts.
        When copying, you can set the accounting date in the budget and the date of payment.
        The copied account takes the draft status, regardless of the status of the copied account.
        Responsible in the copied account will be the user who launched the action.
    """,
    'author': "Ahmed Elgamal",
    'category': 'Accounting',
    'version': '15.0.0.0',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice_views.xml',
        'wizard/account_invoice_copy_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
