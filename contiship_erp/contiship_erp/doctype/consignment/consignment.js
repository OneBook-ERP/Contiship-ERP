// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.ui.form.on("Consignment", {
    refresh(frm) {
        // Set query for containers field in Container Entry child table
        frm.fields_dict.container_entry.grid.get_field("containers").get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    custom_consignment_container_items: 1,
                    disabled: 0
                }
            };
        };
    }
});


