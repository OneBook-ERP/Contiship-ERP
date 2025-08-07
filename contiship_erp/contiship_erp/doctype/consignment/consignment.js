// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.ui.form.on("Consignment", {
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


