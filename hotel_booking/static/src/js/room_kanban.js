/** @odoo-module **/

import KanbanController from 'web.KanbanController';
import KanbanRenderer from 'web.KanbanRenderer';
import KanbanView from 'web.KanbanView';
import KanbanColumn from 'web.KanbanColumn';
import KanbanRecord from 'web.KanbanRecord';
import KanbanModel from 'web.KanbanModel';
import viewRegistry from 'web.view_registry';
import viewUtils from 'web.viewUtils';

// Room

const HotelRoomKanbanRecord = KanbanRecord.extend({
    _render: function () {
        this._super.apply(this, arguments);

        const state = this.record.state_selection.raw_value;
        const stay_state = this.record.stay_state.value

        let backgroundColor;
        if (state === 'clean' && stay_state === 'Vacant') {
            backgroundColor = '#47ff57';
        } else if (state === 'dirty' && stay_state === 'Vacant') {
            backgroundColor = '#ff3636';
        }else if (stay_state === 'Arrived') {
            backgroundColor = '#ffc078';
        }else if (state === 'clean' && stay_state === 'Arrival') {
            backgroundColor = '#bac8ff';
        }else if (stay_state === 'Out of Order') {
            backgroundColor = '#88c0d0';
        }else if (stay_state === 'Stay Over') {
            backgroundColor = 'yellow';
        } else {
            backgroundColor = 'white'; // Default color
        }

        this.$el.css('background-color', backgroundColor);
    },
    /**
     * @override
     * @private
     */
    _openRecord: function () {
        const kanbanBoxesElement = this.el.querySelectorAll('.o_hotel_room_kanban_boxes a');
        if (this.selectionMode !== true && kanbanBoxesElement.length) {
            kanbanBoxesElement[0].click();
        } else {
            this._super.apply(this, arguments);
        }
    },
});

const HotelRoomKanbanRenderer = KanbanRenderer.extend({
    config: _.extend({}, KanbanRenderer.prototype.config, {
        KanbanRecord: HotelRoomKanbanRecord,
    }),
});

const HotelRoomKanbanView = KanbanView.extend({
    config: Object.assign({}, KanbanView.prototype.config, {
        Renderer: HotelRoomKanbanRenderer,
    })
});

viewRegistry.add('hotel_room_kanban', HotelRoomKanbanView);