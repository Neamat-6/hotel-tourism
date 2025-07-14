odoo.define('os_theme_butterfly_enterprise.LegacySearchBar', function (require) {
    "use strict";
    const SearchBar = require('web.SearchBar');


    SearchBar.defaultProps = {
        ...SearchBar.defaultProps,

        isToggleSearch: false,
    };

    SearchBar.props = {
        ...SearchBar.props,
        isToggleSearch: {type: Boolean, optional: true},
    }
});