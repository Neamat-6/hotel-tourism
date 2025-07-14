/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {userService} from "@web/core/user_service";
import {session} from "@web/session";

patch(userService, 'os_theme_butterfly.userService', {
    start(env, {rpc}) {
        const data = this._super(...arguments);
        Object.assign(data, {
            'email': session.user_email
        });
        return data;
    }
});

