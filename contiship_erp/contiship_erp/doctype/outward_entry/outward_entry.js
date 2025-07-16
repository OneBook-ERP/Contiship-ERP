// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.ui.form.on("Outward Entry", {	
    onload(frm) {
        frm.fields_dict['items'].grid.get_field('container').get_query = function(doc, cdt, cdn) {
            if (!frm.doc.consignment){
                frappe.msgprint("Need to set Consigment")
                return                
            }
            const row = locals[cdt][cdn];            
            const selected_containers = (frm.doc.items || [])
                .filter(d => d.container && d.name !== row.name)
                .map(d => d.container);
        
            return {
                query: 'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_containers',
                filters: {
                    consignment: frm.doc.consignment,
                    exclude: selected_containers
                }
            };
        };
        frm.fields_dict['items'].grid.get_field('item').get_query = function(doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            return {
                query: 'contiship_erp.contiship_erp.doctype.outward_entry.outward_entry.get_inward_filter',
                filters: {
                    consignment: frm.doc.consignment,
                    name: row.container
                }
            };
        };
        frm.set_query("consignment", function() {
            if (!frm.doc.customer) {
                frappe.msgprint("Please select a customer first");
                return;
            }
            return {
                filters: {
                    customer: frm.doc.customer,
                    invoice_generated :0
                }
            };
        });
    },
    consignment(frm){
        frm.clear_table("items")
        frm.refresh_field("items")
    }
});


// frappe.ui.form.on('Add On Services', {
//     add_on_item(frm, cdt, cdn) {
//         const row = locals[cdt][cdn];

//         if (!row.add_on_item) return;

//         frappe.call({
//             method: 'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_items_rate',
//             args: {
//                 item: row.add_on_item
//             },
//             callback: function(r) {
//                 if (r.message) {
//                     frappe.model.set_value(cdt, cdn, 'rate', r.message.price || 0);
//                     update_addon_qty_total(frm)                   
//                 }
//             }
//         });
//     }
// });

frappe.ui.form.on('Outward Entry Items', {
    consignment(frm, cdt, cdn) {        
        frappe.model.set_value(cdt, cdn, 'container', null);
    },
    item(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!frm.doc.consignment || !row.container || !row.item) return;

        frappe.call({
            method: 'contiship_erp.contiship_erp.doctype.outward_entry.outward_entry.get_inward_item_details',
            args: {
                consignment: frm.doc.consignment,
                container: row.container,
                item_code: row.item
            },
            callback: function(r) {                
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, 'qty', r.message.qty);
                    frappe.model.set_value(cdt, cdn, 'uom', r.message.uom);
                    frappe.model.set_value(cdt, cdn, 'grade_item', r.message.grade_item);
                    frappe.model.set_value(cdt, cdn, 'grade', r.message.grade);
                }
            }
        });
    },
    // qty(frm) {
    //     update_addon_qty_total(frm);
    // },

    // outward_entry_items_add(frm) {
    //     update_addon_qty_total(frm);
    // },

    // outward_entry_items_remove(frm) {
    //     update_addon_qty_total(frm);
    // }
});



// function update_addon_qty_total(frm) {
//     const total_qty = frm.doc.items?.reduce((sum, item) => sum + (item.qty || 0), 0) || 0;

//     frm.doc.add_on_services_outward?.forEach(row => {
//         frappe.model.set_value(row.doctype, row.name, 'qty', total_qty);
//     });
// }
