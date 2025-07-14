# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.

import re
from odoo import models


class ScssEditor(models.AbstractModel):
    _inherit = 'web_editor.assets'

    # ----------------------------------------------------------
    # Helper
    # ----------------------------------------------------------

    def _get_variable(self, content, variable):
        regex = r'{0}\:?\s(.*?);'.format(variable)
        value = re.search(regex, content)
        return value and value.group(1)

    def _get_variables(self, content, variables):
        return {var: self._get_variable(content, var) for var in variables}

    def _replace_variables(self, content, variables):
        for variable in variables:
            variable_content = '{0}: {1};'.format(
                variable['name'],
                variable['value']
            )
            regex = r'{0}\:?\s(.*?);'.format(variable['name'])
            content = re.sub(regex, variable_content, content)
        return content

    # ----------------------------------------------------------
    # Functions
    # ----------------------------------------------------------

    def get_variables_values(self, url, bundle, variables):
        custom_url = self.make_custom_asset_file_url(url, bundle)
        content = self.get_asset_content(custom_url)
        if not content:
            content = self.get_asset_content(url)
        return self._get_variables(content.decode('utf-8'), variables)

    def replace_variables_values(self, url, bundle, variables):
        original = self.get_asset_content(url).decode('utf-8')
        content = self._replace_variables(original, variables)
        self.with_context(is_os_asset=True).save_asset(url, bundle, content, 'scss')
