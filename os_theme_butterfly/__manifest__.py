# -*- coding: utf-8 -*-
{
    'name': "Butterfly Backend Theme",
    'summary': """
        Butterfly, The most customizable Odoo Backend Theme Ever built, with trending designs and many features.
        Creative & unique including many features like several icons pack, app drawer builder, 
        it is not only a theme but an Odoo backend theme builder.
    """,
    'description': """
        Odoo Theme,
        Odoo Backend Theme,
        Odoo Backend Design,
        Powerful Odoo Backend Theme,
        Premium Odoo Backend Theme,
        Beautiful Odoo Backend Theme,
        New Design Odoo Backend,
        Odoo UI/UX,
        Odoo Design,
        Odoo Backend Template,
        Theme pour Odoo Backend,
    """,
    'sequence': 1,
    'author': "Odoo Stars",
    'maintainer': "Odoo Stars",
    'website': 'http://www.odoo-stars.com',
    'support': 'support@odoo-stars.com',
    'license': 'OPL-1',
    'version': '15.0.0.2',
    'category': 'Themes/Backend',
    'depends': [
        'mail',
        'web',
        'base',
    ],
    'excludes': [
        'web_enterprise',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/ir_ui_menu_views.xml',
        'views/ir_module_views.xml',
        'views/res_lang.xml',
        'views/webclient_templates.xml',
        'views/shapes.xml',
        'views/login.xml',
    ],
    'assets': {

        'web.assets_qweb': [
            'os_theme_butterfly/static/src/**/*.xml',
        ],

        'web.assets_theme_css': [
            'os_theme_butterfly/static/src/theme/fonts/line-awesome/1.3.0/css/line-awesome.css',
            'os_theme_butterfly/static/src/theme/fonts/flag-icons/css/flag-icons.min.css',
            'os_theme_butterfly/static/src/theme/libs/minicolor/jquery.minicolors.css',
            'os_theme_butterfly/static/src/theme/libs/tippy/light-border.css',
        ],

        'web.assets_theme_scss': [
            'os_theme_butterfly/static/src/theme/scss/animations.scss',
            'os_theme_butterfly/static/src/theme/scss/vendors/animate.scss',
            'os_theme_butterfly/static/src/theme/scss/vendors/_simplebar.scss',
            'os_theme_butterfly/static/src/theme/scss/vendors/Osicon/style.scss',
            'os_theme_butterfly/static/src/theme/scss/core/fonts/*.scss',
            'os_theme_butterfly/static/src/theme/scss/core/layouts/*.scss',
            'os_theme_butterfly/static/src/theme/scss/core/utilites/*.scss',
            'os_theme_butterfly/static/src/theme/scss/core/components/*.scss',
            'os_theme_butterfly/static/src/theme/scss/odoo/utilities/*.scss',
            'os_theme_butterfly/static/src/theme/scss/odoo/*.scss',
            'os_theme_butterfly/static/src/theme/scss/odoo/**/*.scss',

        ],

        'web.assets_theme_js': [
            # Odoo

            'os_theme_butterfly/static/src/components/**/*.js',
            'os_theme_butterfly/static/src/core/**/*.js',
            'os_theme_butterfly/static/src/webclient/**/*.js',
            # JS
            'os_theme_butterfly/static/src/theme/libs/osapp/osapp.min.js',
            'os_theme_butterfly/static/src/theme/libs/tippy/popper.min.js',
            'os_theme_butterfly/static/src/theme/libs/tippy/tippy-bundle.umd.min.js',
            'os_theme_butterfly/static/src/theme/libs/simplebar/dist/simplebar.js',
            'os_theme_butterfly/static/src/theme/libs/minicolor/jquery.minicolors.min.js',
        ],

        'web.assets_variables_theme_bootstrap': [
            'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/bootstrap/scss/vendor/_rfs.scss',
            'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/bootstrap/scss/mixins/_utilities.scss',
            'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/bootstrap/scss/_utilities.scss',
            'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/bootstrap/scss/utilities/_api.scss',
            'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/bootstrap/scss/mixins/*.scss',
            'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/utilites/*.scss',

        ],

        'web.assets_theme_bootstrap': [
            'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/components/*.scss',
        ],

        'web.assets_backend': [
            ('replace', 'web/static/src/webclient/webclient_layout.scss', 'os_theme_butterfly/static/src/theme/scss/replace/webclient_layout.scss'),
            ('replace', 'web/static/src/legacy/scss/form_view_extra.scss', 'os_theme_butterfly/static/src/theme/scss/replace/form_view_extra.scss'),
            ('replace', 'web/static/src/search/search_panel/search_view_extra.scss', 'os_theme_butterfly/static/src/theme/scss/replace/search_view_extra.scss'),

            ('prepend', 'os_theme_butterfly/static/src/theme/scss/variables.scss'),
            ('prepend', 'os_theme_butterfly/static/src/theme/scss/variables_commons.scss'),
            ('prepend', 'os_theme_butterfly/static/src/theme/scss/os_custom_variables_fonts.scss'),
            ('prepend', 'os_theme_butterfly/static/src/theme/scss/os_custom_variables.scss'),
            ('prepend', 'os_theme_butterfly/static/src/theme/scss/_variables_to_change.scss'),
            ('prepend', 'os_theme_butterfly/static/src/theme/scss/vendors/Osicon/variables.scss'),
            ('prepend', 'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/functions.scss'),

            ('include', 'web.assets_variables_theme_bootstrap'),
            ('include', 'web.assets_theme_bootstrap'),
            ('before', 'web/static/src/legacy/scss/import_bootstrap.scss', 'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/_variables.scss'),
            ('after', 'web/static/src/legacy/scss/primary_variables.scss', 'os_theme_butterfly/static/src/theme/scss/primary_variables.scss'),
            ('after', 'web/static/src/legacy/scss/secondary_variables.scss', 'os_theme_butterfly/static/src/theme/scss/secondary_variables.scss'),
            ('include', 'web.assets_theme_css'),
            ('include', 'web.assets_theme_scss'),
            ('include', 'web.assets_theme_js'),

        ],

        'web._assets_login': [
            'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/functions.scss',
            'os_theme_butterfly/static/src/theme/scss/vendors/Osicon/variables.scss',
            'os_theme_butterfly/static/src/theme/scss/_variables_to_change.scss',
            'os_theme_butterfly/static/src/theme/scss/variables_commons.scss',
            'os_theme_butterfly/static/src/theme/scss/variables.scss',
            'os_theme_butterfly/static/src/theme/scss/login/os_custom_variables_login.scss',

            # 'web._assets_helpers
            'web/static/lib/bootstrap/scss/_functions.scss',
            'web/static/lib/bootstrap/scss/_mixins.scss',
            'web/static/src/legacy/scss/bs_mixins_overrides.scss',
            'web/static/src/legacy/scss/utils.scss',

            'web/static/lib/bootstrap/scss/_variables.scss',
            'os_theme_butterfly/static/src/theme/scss/extend/bootstrap/_variables.scss',
            'web/static/src/legacy/scss/primary_variables.scss',
            ('include', 'web.assets_variables_theme_bootstrap'),
            ('include', 'web.assets_theme_bootstrap'),
            'web/static/lib/bootstrap/scss/mixins/*.scss',

            ('include', 'web._assets_bootstrap'),
            'os_theme_butterfly/static/src/theme/scss/login/login_styles.scss',
            'os_theme_butterfly/static/src/theme/libs/particles.min.js',

        ],

        # ========= Dark Mode =========

        "web.dark_mode_assets_common": [
            ('include', 'web.assets_common'),
        ],

        "web.dark_mode_assets_backend": [
            ('include', 'web.assets_backend'),
            ('after', 'web/static/lib/bootstrap/scss/_functions.scss', 'os_theme_butterfly/static/src/theme/scss/dark/bs_functions_overridden.dark.scss'),
            ('replace', 'os_theme_butterfly/static/src/theme/scss/variables.scss', 'os_theme_butterfly/static/src/theme/scss/dark/variables.dark.scss'),
            'os_theme_butterfly/static/src/theme/scss/dark/styles/*.scss',

        ],

        'web.assets_backend_prod_only': [
            ('replace', 'web/static/src/main.js', 'os_theme_butterfly/static/src/main.js'),
        ],
    },
    'images': [
        'static/description/img/main_screen.png',
        'static/description/img/main_screenshot.gif'
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'installable': True,
    'price': 120.0,
    'currency': 'USD',
    'live_test_url': 'https://butterfly.odoo-stars.com/r/3Ma',
    'application': True,
    'auto_install': False,
    'post_init_hook': 'icons_post_init_hook',
    'uninstall_hook': '_uninstall_reset_changes',
}
