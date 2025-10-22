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
});

frappe.ui.form.on('Inward Entry Item', {
    onload(frm, cdt, cdn) {
        if (!frm.doc.customer) {
            frappe.throw("Please select a customer.");
        }
    },

    container_size(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.container_size) return;

        let tariff = (frm.doc.customer_tariff_config || []).find(t =>
            (t.container_feet && t.container_feet.toString() === row.container_size.toString()) ||
            (t.lcl_type && t.lcl_type.toString() === row.container_size.toString())
        );

        if (tariff) {
            frappe.model.set_value(cdt, cdn, 'rate', tariff.rate || 0);
            frappe.model.set_value(cdt, cdn, 'service_type', tariff.service_type || 0);
            frappe.model.set_value(cdt, cdn, 'enable_75_rule', tariff.enable_75_rule || 0);
            frappe.model.set_value(cdt, cdn, 'enable_875_rule', tariff.enable_875_rule || 0);
            frappe.model.set_value(cdt, cdn, 'after_75_discounted_rate', tariff.after_75_discounted_rate || 0);
            frappe.model.set_value(cdt, cdn, 'after_875discounted_rate', tariff.after_875discounted_rate || 0);
            frappe.model.set_value(cdt, cdn, 'minimum_commitmentnoofdays', tariff.minimum_commitmentnoofdays || 0);
            frm.refresh_field("inward_entry_items");
        }
    }
});

frappe.ui.form.on('Add On Services', {
    add_on_item(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.add_on_item) return;
        frappe.call({
            method: 'contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.get_items_rate',
            args: {
                item: row.add_on_item,
                tariffs: frm.doc.customer_tariff_config
            },
            callback: function(r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, 'rate', r.message.price || 0);                                     
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
        if(row.service_type){
            frappe.call({
                method: "contiship_erp.custom.traffic_custom.fetch_item_data",
                args: {
                    service_type: row.service_type
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, "rent_type", r.message.rent_type);
                        frappe.model.set_value(cdt, cdn, "square_feet_size", r.message.square_feet_size);
                        frappe.model.set_value(cdt, cdn, "additional_sqft_size", r.message.additional_sqft_size);
                        frappe.model.set_value(cdt, cdn, "add_on_type", r.message.add_on_type);
                        frappe.model.set_value(cdt, cdn, "add_on_service", r.message.add_on_service);
                        frappe.model.set_value(cdt, cdn, "container_feet", r.message.container_feet);
                        frappe.model.set_value(cdt, cdn, "lcl_type", r.message.lcl_type);
                        frappe.model.set_value(cdt, cdn, "minimum_commitmentnoofdays", r.message.min_commitment);
                        frappe.model.set_value(cdt, cdn, "rate", r.message.rate);
                        frm.refresh_field("customer_tariff_config");
                    }
                }
            });
        }
    },
    rate(frm, cdt, cdn) {
        reapply_tariffs_to_containers(frm, cdt, cdn);
    },
    enable_75_rule(frm, cdt, cdn) {
        reapply_tariffs_to_containers(frm, cdt, cdn);
    },   
    enable_875_rule(frm, cdt, cdn) {
        reapply_tariffs_to_containers(frm, cdt, cdn);
    },
    after_875discounted_rate(frm, cdt, cdn) {
        reapply_tariffs_to_containers(frm, cdt, cdn);
    },
    after_75_discounted_rate(frm, cdt, cdn) {
        reapply_tariffs_to_containers(frm, cdt, cdn);
    },
    minimum_commitmentnoofdays(frm, cdt, cdn) {
        reapply_tariffs_to_containers(frm, cdt, cdn);
    }
});


function reapply_tariffs_to_containers(frm, cdt, cdn) {   
    (frm.doc.inward_entry_items || []).forEach(row => {
        if (row.container_size) {
            let tariff = (frm.doc.customer_tariff_config || []).find(t =>
                (t.container_feet && t.container_feet.toString() === row.container_size.toString()) ||
                (t.lcl_type && t.lcl_type.toString() === row.container_size.toString())
            );           

            if (tariff) {         
                frappe.model.set_value(row.doctype, row.name, 'rate', tariff.rate || 0);
                frappe.model.set_value(row.doctype, row.name, 'service_type', tariff.service_type || 0);
                frappe.model.set_value(row.doctype, row.name, 'enable_75_rule', tariff.enable_75_rule || 0);
                frappe.model.set_value(row.doctype, row.name, 'enable_875_rule', tariff.enable_875_rule || 0);
                frappe.model.set_value(row.doctype, row.name, 'after_75_discounted_rate', tariff.after_75_discounted_rate || 0);
                frappe.model.set_value(row.doctype, row.name, 'after_875discounted_rate', tariff.after_875discounted_rate || 0);
                frappe.model.set_value(row.doctype, row.name, 'minimum_commitmentnoofdays', tariff.minimum_commitmentnoofdays || 0);
            }
        }
    });
    frm.refresh_field("inward_entry_items");
}

