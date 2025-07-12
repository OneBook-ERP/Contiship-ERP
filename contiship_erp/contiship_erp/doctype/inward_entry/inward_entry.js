// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inward Entry', {
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
    consignment(frm) {
        if (frm.doc.consignment) {
            frm.set_value('container', '');
            frm.refresh_field('container');
        }
    },
    container(frm){      
        get_arrival_date(frm)
    }
});

// frappe.ui.form.on('Add On Services', {
//     add_on_item(frm,cdt,cdn){
//         frappe.call({
//             method: 'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_items',
//             args: {
//                 'consignment': frm.doc.consignment
//             },
//             callback: function(r) {
//                 if (r.message) {                    
//                     let display = `${frm.doc.consignment || ''} - ${r.message.item_name || r.message.item_code || ''}`;
//                     frm.set_df_property('container', 'description', display);
//                 }
//             }
//         })
//     }
// });


frappe.ui.form.on('Inward Entry', 'container', function(frm, cdt, cdn) {
    if (frm.doc.container) {        
        frappe.call({
            method: 'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_container_details',
            args: {
                'container_id': frm.doc.container
            },
            callback: function(r) {
                if (r.message) {                    
                    let display = `${frm.doc.consignment || ''} - ${r.message.item_name || r.message.item_code || ''}`;
                    frm.set_df_property('container', 'description', display);
                }
            }
        });
    } else {
        frm.set_df_property('container', 'description', '');
    }
});

function get_arrival_date(frm){
    frappe.call({
        method:'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_arrival_date',
        args:{
            "name":frm.doc.container
        },
        callback: function(r){
            if(r.message){
                frm.set_value("arrival_date",r.message)
            }
        }
    })
}