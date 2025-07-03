/** @odoo-module **/
import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';
import framework from 'web.framework';
const { Gui } = require('point_of_sale.Gui');
const { _t } = require('web.core');
const { useState } = owl;
class RoomChargePopup extends AbstractAwaitablePopup {
  constructor() {
    super(...arguments);
    this.roomState = useState({
      availbleRoom: false ,
      folioNumber: 'initial',
      guestName: '',
      confirmText: 'Charge',
      cancelText: 'Cancel',
      title: 'Room charge',
      body: '',
    });
  }

  async confirm() {
    console.log('Room Charge');
    const currentOrder = this.env.pos.get_order();
    let roomName = $('#room-name').val();
    this.rpc({
      model: 'booking.folio.line',
      method: 'create_from_pos_order',
      args: [currentOrder.export_as_JSON(), roomName],
    });
    const RoomId = await this.rpc({
        model: 'hotel.room',
        method: 'search_read',
        args: [[['name', '=', roomName]]],
        });
    if (RoomId.length > 0) {
        currentOrder.hotel_room_id = RoomId[0].id;
        currentOrder.hotel_room_name = RoomId[0].name;
    }
    // close the popup and continue with the payment
    return super.confirm();

  }

  async searchRoom() {
    framework.blockUI();
    let roomName = $('#room-name').val();
    let domain = [['name', '=', roomName]];
    let room = await this.rpc({
      model: 'hotel.room',
      method: 'search_read',
      args: [domain, []],
    });
    if (room.length > 0) {
      let roomFolio = await this.rpc({
        model: 'booking.folio',
        method: 'search_read',
        args: [[['id', '=', room[0].folio_id[0]]], []],
      });
      if (roomFolio.length > 0 && roomFolio[0].state == "checked_in") {
        this.roomState.availbleRoom = true;
        this.roomState.folioNumber = roomFolio[0].name;
        this.roomState.guestName = roomFolio[0].partner_id[1];
        this.props = { ...this.props,...this.roomState };
      }
      else{
        Gui.showPopup('ErrorPopup', {
            title: _t('No Room Folio'),
            body: _t('This room is not checked in.'),
        });
      }
    }

    else {
      this.roomState.folioNumber = "";
      this.props = { ...this.props,...this.roomState };
    }
    framework.unblockUI();
  }
}
//Create products popup
RoomChargePopup.template = 'RoomChargePopup';
RoomChargePopup.defaultProps = {
  confirmText: 'Ok',
  cancelText: 'Cancel',
  title: 'Room charge',
  body: '',
  availbleRoom: false,
  folioNumber: 'initial',
};
Registries.Component.add(RoomChargePopup);
//   return RoomChargePopup;
export default RoomChargePopup;