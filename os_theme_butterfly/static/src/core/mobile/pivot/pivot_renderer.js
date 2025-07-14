/** @odoo-module **/

import config from "web.config";

if (!config.device.isMobile) {
    return;
}
import {PivotRenderer} from "@web/views/pivot/pivot_renderer";
import {useEffect} from "@web/core/utils/hooks";

import {PivotGroupByMenu} from "@web/views/pivot/pivot_group_by_menu";
import {patch} from "web.utils";

patch(PivotRenderer.prototype, "pivot_mobile", {
    setup() {
        this._super();
        useEffect(() => {
            const tooltipElems = this.el.querySelectorAll("*[data-tooltip]");
            for (const el of tooltipElems) {
                el.removeAttribute("data-tooltip");
                el.removeAttribute("data-tooltip-position");
            }
        });

    },
    _updateTooltip() {
    },

    _getPadding(cell) {
        return 5 + cell.indent * 5;
    },
});

patch(PivotGroupByMenu.prototype, "pivot_mobile", {
    _onClickMenuGroupBy(fieldName, interval, ev) {
        if (!ev.currentTarget.classList.contains("o_pivot_field_selection")) {
            this._super(...arguments);
        } else {
            ev.stopPropagation();
        }
    },
});
