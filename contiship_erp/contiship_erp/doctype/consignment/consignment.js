// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.ui.form.on("Consignment", {
    refresh(frm) {        
        frm.fields_dict.container_entry.grid.get_field("containers").get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    custom_consignment_container_items: 1,
                    disabled: 0
                }
            };
        };
    },
    customer(frm){
        if(frm.doc.customer){
        frappe.call({
            method: 'contiship_erp.contiship_erp.doctype.consignment.consignment.get_traffic_config',
            args: {
                'customer': frm.doc.customer
            },
            callback: function(r) {
                if (r.message) {                                    
                   frm.set_value("customer_traffic_config", r.message.custom_customer_traffic_config);
                   frm.refresh_field("customer_traffic_config");
                }
            }
        })
    }
    }
});


