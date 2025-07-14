odoo.define('os_theme_butterfly.KanbanRendererUtilities', function () {
    "use strict";
    return {

        _getTabPosition(tabs, moveToIndex, $tabsContainer) {
            this._getTabJustification(tabs, $tabsContainer);
            this._getTabScrollPosition(tabs, moveToIndex, $tabsContainer);
        },

        _getTabScrollPosition(tabs, moveToIndex, $tabsContainer) {
            if (tabs.length) {
                const lastItemIndex = tabs.length - 1;
                let scrollToLeft = 0;
                for (let i = 0; i < moveToIndex; i++) {
                    const columnWidth = this._getTabWidth(tabs[i]);
                    if (moveToIndex !== lastItemIndex && i === moveToIndex - 1) {
                        const partialWidth = 0.75;
                        scrollToLeft += columnWidth * partialWidth;
                    } else {
                        scrollToLeft += columnWidth;
                    }
                }
                $tabsContainer.scrollLeft(scrollToLeft);
            }
        },


        _getTabJustification(tabs, $tabsContainer) {
            if (tabs.length) {
                const widthChilds = tabs.reduce((total, column) => total + this._getTabWidth(column), 0);
                $tabsContainer.toggleClass('justify-content-between', $tabsContainer.outerWidth() >= widthChilds);
            }
        },

        _getTabWidth(tab) {
        }
    };
});
