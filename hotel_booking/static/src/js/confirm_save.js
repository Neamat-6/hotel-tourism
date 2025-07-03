odoo.define('hotel_booking.ConfirmSave', function (require) {
    "use strict";

    const FormController = require('web.FormController');
    const Dialog = require('web.Dialog');

    // Store a reference to the original _saveRecord method
    const originalSaveRecord = FormController.prototype._saveRecord;

    FormController.include({
        _saveRecord: function () {
            const self = this;

            if (self._isSaving) {
                return Promise.resolve();
            }

            self._isSaving = true;

            return new Promise((resolve, reject) => {
                Dialog.confirm(self, "Are you sure you want to save this record?", {
                    title: "Confirm Save",
                    confirm_callback: async () => {
                        try {
                            console.log(">>> Confirm button clicked");

                            // Call the original _saveRecord method
                            await originalSaveRecord.apply(self, arguments);

                            console.log(">>> Record saved successfully!");

//                            resolve();
                        } catch (error) {
                            console.error(">>> ERROR during save", error);
                            reject(error);
                        } finally {
                            self._isSaving = false;
                        }
                    },
                    cancel_callback: () => {
                        self.discardChanges();
                        console.log(">>> Save canceled.");

                        self._isSaving = false;

                        reject();
                    },
                });
            });
        },
    });
});