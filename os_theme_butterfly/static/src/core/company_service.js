/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {companyService} from "@web/webclient/company_service";

patch(companyService, 'os_theme_butterfly.companyService', {
    start(env, {user, router, cookie}) {
        const data = this._super(...arguments);
        let currentCompany = data.currentCompany;
        Object.assign(data, {
            'logo_white': `/web/image/res.company/${currentCompany.id}/os_theme_logo_white`,
            'logo_dark': `/web/image/res.company/${currentCompany.id}/os_theme_logo_dark`,
            'logo_small': `/web/image/res.company/${currentCompany.id}/os_theme_logo_small`,

        });
        return data;
    }
});

