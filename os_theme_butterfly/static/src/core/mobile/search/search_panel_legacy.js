odoo.define("os_theme_butterfly.LegacySearchPanelMobile", function (require) {
    "use strict";

    const {device} = require("web.config");

    if (!device.isMobile) {
        return;
    }
    const {patch} = require('web.utils');
    const SearchPanel = require("web.searchPanel");
    const {Portal} = owl.misc;


    function getNmaes(values) {
        const names = [];
        for (const [_, value] of values) {
            if (value.checked) {
                names.push(value.display_name);
            }
        }
        return names;
    }

    const is_filter = (element) => element.type === "filter";

    patch(SearchPanel.prototype, "os_theme_butterfly.Legacy.SearchPanel.Mobile", {
        setup() {
            this._super(...arguments);
            this.state.showMobileSearch = false;
        },

        _getCategories() {
            const active_categories = this.model.get("sections",
                (section) => section.type === "category" && section.activeValueId
            );
            const categs = [];
            for (const category of active_categories) {
                const ancestor_value_ids = this._getAncestorValueIds(
                    category,
                    category.activeValueId
                );
                const ordered_category_names = [
                    ...ancestor_value_ids,
                    category.activeValueId,
                ].map(
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
            const filters = this.model.get("sections", is_filter);
            const res = [];
            for (const {groups, values, icon, color} of filters) {
                let filter_values;
                if (groups) {
                    filter_values = Object.keys(groups)
                        .map((groupId) =>
                            getNmaes(groups[groupId].values)
                        )
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

    patch(SearchPanel, "os_theme_butterfly.Legacy.SearchPanel.Mobile", {
        template: "os_theme_butterfly.Legacy.SearchPanel.Mobile",
        components: {
            ...SearchPanel.components,
            Portal,
        },
    });
});
