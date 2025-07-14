/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Mutex} from "@web/core/utils/concurrency";
import {useService} from "@web/core/utils/hooks";
import {customComputeAppsAndMenuItems} from "@os_theme_butterfly/webclient/menus/menu_helpers";
import {ControllerNotFoundError} from "@web/webclient/actions/action_service";
import {OsViewApps} from "./os_view_apps";

const {Component, tags} = owl;

export const ViewAppsService = {
    dependencies: ["action", "router"],
    start(env) {
        const mutex = new Mutex();
        let is_displayed = false;
        let hasAction = false;

        class ViewAppsAction extends Component {
            setup() {
                this.router = useService("router");
                this.menus = useService("menu");
                this.MenuProps = customComputeAppsAndMenuItems(this.menus.getMenuAsTree("root"));
            }

            async mounted() {
                const {breadcrumbs = []} = this.env.config;
                is_displayed = true;
                hasAction = breadcrumbs.length > 0;

                this.router.pushState({menu_id: undefined}, {lock: false, replace: true});
                this.env.bus.trigger("APPS-MENU-TOGGLED");
                var url = window.location.href
                if (url.includes("apps_drawer_view")) {
                    $('#icon_bookmark').addClass("text-warning").removeClass('osi-bookmark').addClass('osi-bookmark-fill');
                } else {
                    $('#icon_bookmark').removeClass("text-warning").removeClass('osi-bookmark-fill').addClass('osi-bookmark');
                }
            }

            patched() {

            }

            willUnmount() {
                is_displayed = false;
                hasAction = false;
                const currentMenuId = this.menus.getCurrentApp();
                if (currentMenuId) {
                    this.router.pushState({menu_id: currentMenuId.id}, {lock: true});
                }
                this.env.bus.trigger("APPS-MENU-TOGGLED");
            }
        }

        ViewAppsAction.components = {OsViewApps};
        ViewAppsAction.target = "current";
        ViewAppsAction.template = tags.xml`<OsViewApps t-props="MenuProps"/>`;

        registry.category("actions").add("apps_drawer_view", ViewAppsAction);

        return {
            get is_displayed() {
                return is_displayed;
            },
            get hasAction() {
                return hasAction;
            },
            toggleBookmark() {
                var url = window.location.href
                if (url.includes("apps_drawer_view")) {
                    $('#icon_bookmark').addClass("text-warning").removeClass('osi-bookmark').addClass('osi-bookmark-fill');
                } else {
                    $('#icon_bookmark').removeClass("text-warning").removeClass('osi-bookmark-fill').addClass('osi-bookmark');
                }
            },
            async toggleView(display) {
                return mutex.exec(async () => {
                    display = display === undefined ? !is_displayed : Boolean(display);
                    if (display !== is_displayed) {
                        if (display) {
                            await env.services.action.doAction("apps_drawer_view");
                        } else {
                            try {
                                await env.services.action.restore();
                            } catch (err) {
                                if (!(err instanceof ControllerNotFoundError)) {
                                    throw err;
                                }
                            }
                        }
                    }
                    return new Promise((r) => setTimeout(r));
                });
            },
        };
    },
};

registry.category("services").add("view_apps", ViewAppsService);
