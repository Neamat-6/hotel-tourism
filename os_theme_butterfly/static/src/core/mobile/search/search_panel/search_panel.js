/** @odoo-module **/
import config from "web.config";

if (!config.device.isMobile) {
    return;
}
import {SearchPanel} from "@web/search/search_panel/search_panel";
import {patch} from "@web/core/utils/patch";
const {Portal} = owl.misc;

const getNmaes = (values) => {
    const names = [];
    for (const [, value] of values) {
        if (value.checked) {
            names.push(value.display_name);
        }
    }
    return names;
};
const is_filter = (element) => element.type === "filter";
const is_active_category = (element) => element.type === "category" && element.activeValueId;


patch(SearchPanel.prototype, "os_theme_butterfly.SearchPanelMobile", {
    setup() {
        this._super(...arguments);
        this.state.showMobileSearch = false;
    },


    _getCategories() {
        const active_categories = this.env.searchModel.getSections(is_active_category);
        const categs = [];
        for (const category of active_categories) {
            const ancestor_value_ids = this.getAncestorValueIds(category, category.activeValueId);
            const ordered_category_names = [...ancestor_value_ids, category.activeValueId].map(
                (valueId) => category.values.get(valueId).display_name
            );
            categs.push({
                values: ordered_category_names,
                icon: category.icon,
                color: category.color,
            });
        }
        return categs;
    },


    _getFilters() {
        const filters = this.env.searchModel.getSections(is_filter);
        const res = [];
        for (const {groups, values, icon, color} of filters) {
            let filter_values;
            if (groups) {
                filter_values = Object.keys(groups)
                    .map((groupId) => getNmaes(groups[groupId].values))
                    .flat();
            } else if (values) {
                filter_values = getNmaes(values);
            }
            if (filter_values.length) {
                res.push({values: filter_values, icon, color});
            }
        }
        return res;
    },
});

patch(SearchPanel, "os_theme_butterfly.SearchPanelMobile", {
    template: "os_theme_butterfly.SearchPanelMobile",
    components: {
        ...SearchPanel.components,
        Portal,
    },
});
