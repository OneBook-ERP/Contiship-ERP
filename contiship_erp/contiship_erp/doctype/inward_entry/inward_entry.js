// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inward Entry', {
    refresh(frm) {
        // Set up the query for the container field
        frm.set_query('container', function() {
            return {
                query: 'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_containers',
                filters: {
                    'consignment': frm.doc.consignment
                }
            };
        });
    },
    
    // When consignment is selected, refresh the container options
    consignment(frm) {
        if (frm.doc.consignment) {
            frm.set_value('container', '');
            frm.refresh_field('container');
        }
    }
});

// Format the display of the container field
frappe.ui.form.on('Inward Entry', 'container', function(frm, cdt, cdn) {
    if (frm.doc.container) {
        // Fetch the container details to get the item name
        frappe.call({
            method: 'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_container_details',
            args: {
                'container_id': frm.doc.container
            },
            callback: function(r) {
                if (r.message) {
                    // Update the display to show both consignment and item name
                    let display = `${frm.doc.consignment || ''} - ${r.message.item_name || r.message.item_code || ''}`;
                    frm.set_df_property('container', 'description', display);
                }
            }
        });
    } else {
        frm.set_df_property('container', 'description', '');
    }
});