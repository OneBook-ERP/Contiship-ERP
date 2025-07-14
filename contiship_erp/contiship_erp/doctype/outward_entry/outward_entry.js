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
        method: 'contiship_erp.contiship_erp.doctype.outward_entry.outward_entry.get_inward_items',
        args: {
            "consignment": frm.doc.consignment,
            "name": frm.doc.container
        },
        callback: function (r) {
            if (r.message) {
                console.log(r);
                // frm.set_value("date", r.message.arrival_date);                
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


frappe.ui.form.on('Add On Services', {
    add_on_item(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (!row.add_on_item) return;

        frappe.call({
            method: 'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_items_rate',
            args: {
                item: row.add_on_item
            },
            callback: function(r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, 'rate', r.message.price || 0);
                    update_addon_qty_total(frm)                   
                }
            }
        });
    }
});

frappe.ui.form.on('Outward Entry Items', {
    qty: function(frm) {
        update_addon_qty_total(frm);
    },
    inward_entry_items_add: function(frm) {
        update_addon_qty_total(frm);
    },
    inward_entry_items_remove: function(frm) {
        update_addon_qty_total(frm);
    }
});

function update_addon_qty_total(frm) {
    const total_qty = frm.doc.items?.reduce((sum, item) => sum + (item.qty || 0), 0) || 0;

    frm.doc.add_on_services_outward?.forEach(row => {
        frappe.model.set_value(row.doctype, row.name, 'qty', total_qty);
    });
}
