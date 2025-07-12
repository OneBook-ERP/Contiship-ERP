// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.ui.form.on("Outward Entry", {
	refresh(frm) {        
        frm.set_query('container', function() {
            return {
                query: 'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_containers',
                filters: {
                    'consignment': frm.doc.consignment
                }
            };
        });
    },
    container(frm){      
        get_arrival_date(frm)
    }
});


function get_arrival_date(frm) {
    frappe.call({
        method: 'contiship_erp.contiship_erp.doctype.outward_entry.outward_entry.get_arrival_date',
        args: {
            "consignment": frm.doc.consignment,
            "name": frm.doc.container
        },
        callback: function (r) {
            if (r.message) {
                console.log(r);
                frm.set_value("date", r.message.arrival_date);                
                frm.clear_table("items");
                
                (r.message.inward_items || []).forEach(item => {
                    let row = frm.add_child("items");
                    row.item = item.item;
                    row.qty = item.qty;
                    row.uom = item.uom;
                    row.batch = item.batch;
                });

                frm.refresh_field("items");
            }
        }
    });
}

