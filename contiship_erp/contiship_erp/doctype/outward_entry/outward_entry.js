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
                    invoice_generated :0,
                    docstatus : 1
                }
            };
        });
    },
    consignment(frm){
        frm.clear_table("items")
        frm.refresh_field("items")
        if (frm.doc.consignment){        
            frappe.call({
                method: 'contiship_erp.contiship_erp.doctype.outward_entry.outward_entry.get_all_inward_items',
                args: {
                    consignment: frm.doc.consignment,                    
                },
                callback: function(r) {                
                    if (r.message && Array.isArray(r.message)) {
                        r.message.forEach(item => {
                            let row = frm.add_child("items", {
                                container: item.name,
                                container_name : item.container,
                                item: item.item,
                                stock_qty: item.qty,
                                uom: item.uom,
                                grade_item: item.grade_item,
                                grade: item.grade,
                                crossing_item: item.crossing_item
                            });
                        });
                        frm.refresh_field("items");
                    }
                }
            })
        }
    },
    customer(frm){
        if (frm.doc.customer){
            get_inward_items(frm)
        }
    }
});

function get_inward_items(frm){
    frappe.call({
        method: "contiship_erp.contiship_erp.doctype.outward_entry.outward_entry.get_inward_html_table",
        args: {
            customer: frm.doc.customer
        },
        callback: function (r) {
            if (r.message) {
                frm.set_df_property('consignment_data', 'options', r.message);
                frm.refresh_field('consignment_data');
            }
        }
    });
}

frappe.ui.form.on('Outward Entry Items', {
    // consignment(frm, cdt, cdn) {        
    //     frappe.model.set_value(cdt, cdn, 'container', null);
    // },
    container(frm, cdt, cdn) {
        const row = locals[cdt][cdn];    
        frappe.model.set_value(cdt, cdn, 'item', null);    
        frappe.model.with_doc("Inward Entry Item", row.container).then(() => {
            const doc = frappe.model.get_doc("Inward Entry Item", row.container);
            frappe.model.set_value(cdt, cdn, 'container_name', doc.container);
        })
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
                    frappe.model.set_value(cdt, cdn, 'stock_qty', r.message.qty);
                    frappe.model.set_value(cdt, cdn, 'uom', r.message.uom);
                    frappe.model.set_value(cdt, cdn, 'grade_item', r.message.grade_item);
                    frappe.model.set_value(cdt, cdn, 'grade', r.message.grade); 
                    frappe.model.set_value(cdt, cdn, 'crossing_item', r.message.crossing_item);                  
                }
            }
        });
    },   
});