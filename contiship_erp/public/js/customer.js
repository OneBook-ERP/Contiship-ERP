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
        if (row.service_type) {
            frappe.call({
                method: "contiship_erp.custom.traffic_custom.fetch_item_data",
                args: {
                    service_type: row.service_type
                },
                callback: function (r) {
                    if (r.message){
                        console.log(r.message)
                        frappe.model.set_value(cdt, cdn, "rent_type", r.message.rent_type);
                        frappe.model.set_value(cdt, cdn, "square_feet_size", r.message.square_feet_size);
                        frappe.model.set_value(cdt, cdn, "ton_size", r.message.ton_size);
                        frappe.model.set_value(cdt, cdn, "add_on_type", r.message.add_on_type);
                        frappe.model.set_value(cdt, cdn, "add_on_service", r.message.add_on_service);
                        frappe.model.set_value(cdt, cdn, "container_feet", r.message.container_feet);
                        frappe.model.set_value(cdt, cdn, "minimum_commitmentnoofdays", r.message.min_commitment);
                        frappe.model.set_value(cdt, cdn, "rate", r.message.rate);                        
                        frm.refresh_field("custom_customer_traffic_config");
                        // if(r.message.sqft_value === 80 || r.message.sqft_value === 40) {
                        //     frm.fields_dict.custom_customer_traffic_config.grid.get_field("container_sqft").hidden = 1;
                        //     frm.fields_dict.custom_customer_traffic_config.grid.get_field("container_feet").hidden = 1;
                        //     frm.fields_dict.custom_customer_traffic_config.grid.get_field("ton_based").hidden = 0;
                        //     frm.fields_dict.custom_customer_traffic_config.grid.get_field("ton_based_sqft").df.label = "Ton SQFT";
                        // } else {
                        //     frm.fields_dict.custom_customer_traffic_config.grid.get_field("container_sqft").hidden = 0;
                        //     frm.fields_dict.custom_customer_traffic_config.grid.get_field("container_feet").hidden = 0;
                        //     frm.fields_dict.custom_customer_traffic_config.grid.get_field("ton_based").hidden = 1;
                        //     frm.fields_dict.custom_customer_traffic_config.grid.get_field("ton_based_sqft").df.label = "Container SQFT";
                        // }
                    }
                }
            });
        }
    }
});