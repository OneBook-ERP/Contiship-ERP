frappe.ui.form.on("Customer", {
    refresh(frm) {
        frm.fields_dict.custom_customer_traffic_config.grid.get_field("service_type").get_query = function(doc, cdt, cdn) {
            return {
                query: "contiship_erp.custom.traffic_custom.get_valid_service_items"
            };
        };        
    }
});

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
                        // Set values if validation passes
                        frappe.model.set_value(cdt, cdn, "rent_type", r.message.rent_type);
                        frappe.model.set_value(cdt, cdn, "square_feet_size", r.message.square_feet_size);
                        frappe.model.set_value(cdt, cdn, "additional_sqft_size", r.message.additional_sqft_size);
                        frappe.model.set_value(cdt, cdn, "add_on_type", r.message.add_on_type);
                        frappe.model.set_value(cdt, cdn, "add_on_service", r.message.add_on_service);
                        frappe.model.set_value(cdt, cdn, "container_feet", r.message.container_feet);
                        frappe.model.set_value(cdt, cdn, "lcl_type", r.message.lcl_type);
                        frappe.model.set_value(cdt, cdn, "minimum_commitmentnoofdays", r.message.min_commitment);
                        frappe.model.set_value(cdt, cdn, "rate", r.message.rate);
                        frm.refresh_field("custom_customer_traffic_config");
                    }
                }
            });
        }
    }
});

