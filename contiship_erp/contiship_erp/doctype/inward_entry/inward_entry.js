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
    },
    customer(frm){
        if(frm.doc.customer){
        frappe.call({
            method: 'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_traffic_config',
            args: {
                'customer': frm.doc.customer
            },
            callback: function(r) {
                if (r.message) {                                    
                   frm.set_value("customer_tariff_config", r.message.custom_customer_traffic_config);
                   frm.refresh_field("customer_tariff_config");
                }
            }
        })
        }
    },
    onload(frm) {
        frm.fields_dict['add_on_services_inward'].grid.get_field('add_on_item').get_query = function(doc, cdt, cdn) {            
            let add_on_items = [];

            (frm.doc.customer_tariff_config || []).forEach(config => {               
                if (config.rent_type === "Add On") {
                    add_on_items.push(config.service_type);
                }
            });
            return {
                filters: [
                    ['name', 'in', add_on_items]
                ]
            };
        };
    },
    // boeinvoice_no(frm){
    //     frm.doc.consignment = frm.doc.boeinvoice_no
    // }
});

frappe.ui.form.on('Inward Entry Item', {
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
    const line_item_count = frm.doc.inward_entry_items?.length || 0;

    frm.doc.add_on_services_inward?.forEach(row => {
        frappe.model.set_value(row.doctype, row.name, 'qty', line_item_count);
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

frappe.ui.form.on("Customer Traffic Config", {
    service_type: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];        
        if (row.service_type) {
            frappe.call({
                method: "contiship_erp.custom.traffic_custom.fetch_item_data",
                args: {
                    service_type: row.service_type
                },
                callback: function (r) {
                    if (r.message){
                        console.log(r.message);
                        frappe.model.set_value(cdt, cdn, "rent_type", r.message.rent_type);
                        frappe.model.set_value(cdt, cdn, "square_feet_size", r.message.square_feet_size);
                        frappe.model.set_value(cdt, cdn, "ton_size", r.message.ton_size);
                        frappe.model.set_value(cdt, cdn, "add_on_type", r.message.add_on_type);
                        frappe.model.set_value(cdt, cdn, "add_on_service", r.message.add_on_service);
                        frappe.model.set_value(cdt, cdn, "container_feet", r.message.container_feet);
                        frappe.model.set_value(cdt, cdn, "minimum_commitmentnoofdays", r.message.min_commitment);
                        frappe.model.set_value(cdt, cdn, "rate", r.message.rate);                        
                        frm.refresh_field("custom_customer_traffic_config");                                              
                    }
                }
            });
        }
    },       
});