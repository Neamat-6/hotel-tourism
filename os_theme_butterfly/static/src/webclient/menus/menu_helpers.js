/** @odoo-module **/

/**
 * Traverses the given menu tree, executes the given callback for each node with
 * the node itself and the list of its ancestors as arguments.
 *
 * @param {Object} tree tree of menus as exported by the menus service
 * @param {Function} cb
 * @param {[Object]} [parents] the ancestors of the tree root, if any
 */
function traverseMenuTree(tree, cb, parents = []) {
    cb(tree, parents);
    tree.childrenTree.forEach((c) => traverseMenuTree(c, cb, parents.concat([tree])));
}

/**
 * Computes the "apps" and "menuItems" from a given menu tree.
 *
 * @param {Object} menuTree tree of menus as exported by the menus service
 * @returns {Object} with keys "apps" and "menuItems" (HomeMenu props)
 */
export function customComputeAppsAndMenuItems(menuTree) {
    const apps = [];
    const menuItems = [];
    traverseMenuTree(menuTree, (menuItem, parents) => {
        if (!menuItem.id || !menuItem.actionID) {
            return;
        }
        const isApp = menuItem.id === menuItem.appID;
        const item = {
            parents: parents
                .slice(1)
                .map((p) => p.name)
                .join(" / "),
            label: menuItem.name,
            id: menuItem.id,
            xmlid: menuItem.xmlid,
            actionID: menuItem.actionID,
            appID: menuItem.appID,
        };
        if (isApp) {
            item.webIconFont = menuItem.webIconFont;
            item.webIconStyle = menuItem.webIconStyle;
            item.webIconColor = menuItem.webIconColor;
            item.webShapeColor = menuItem.webShapeColor;
            item.webIconChanged = menuItem.webIconChanged;
            item.webImageIcon = menuItem.webImageIcon;
            item.webIcon = menuItem.webIcon;
            item.hasNoAction = menuItem.hasNoAction;

            if (menuItem.webIconData) {
                item.webIconData = menuItem.webIconData;
            } else {
                const [iconClass, color, backgroundColor] = (menuItem.webIcon || "").split(",");
                if (backgroundColor !== undefined) {
                    item.webIcon = {iconClass, color, backgroundColor};
                } else {
                    item.webIconData = "/os_theme_butterfly/static/src/img/default_icon_app.png";
                }
            }
        } else {
            item.menuID = parents[1].id;
        }
        if (isApp) {
            apps.push(item);
        } else {
            menuItems.push(item);
        }
    });
    return {apps, menuItems};
}
