/** @odoo-module **/

const {Component, hooks} = owl;

export class OsScrollToTop extends Component {
    setup() {
        super.setup();
    }

    onClick() {
        $(".o_content").animate({scrollTop: 0}, 500);
    }

}

OsScrollToTop.template = 'os_theme_butterfly.os_scroll_to_top';
