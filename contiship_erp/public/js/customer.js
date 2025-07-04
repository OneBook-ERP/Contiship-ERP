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
                        frappe.model.set_value(cdt, cdn, "ton_based", r.message.sqft_value);
                        frappe.model.set_value(cdt, cdn, "ton_based_sqft", r.message.ton_sqft);
                        frappe.model.set_value(cdt, cdn, "container_sqft", r.message.container_sqft);
                        frappe.model.set_value(cdt, cdn, "container_feet", r.message.container_feet);
                        frappe.model.set_value(cdt, cdn, "minimum_commitmentnoofdays", r.message.min_commitment);
                        frm.refresh_field("custom_customer_traffic_config");
                        if(r.message.sqft_value === 80 || r.message.sqft_value === 40) {
                            frm.fields_dict.custom_customer_traffic_config.grid.get_field("container_sqft").hidden = 1;
                            frm.fields_dict.custom_customer_traffic_config.grid.get_field("container_feet").hidden = 1;
                            frm.fields_dict.custom_customer_traffic_config.grid.get_field("ton_based").hidden = 0;
                            frm.fields_dict.custom_customer_traffic_config.grid.get_field("ton_based_sqft").df.label = "Ton SQFT";
                        } else {
                            frm.fields_dict.custom_customer_traffic_config.grid.get_field("container_sqft").hidden = 0;
                            frm.fields_dict.custom_customer_traffic_config.grid.get_field("container_feet").hidden = 0;
                            frm.fields_dict.custom_customer_traffic_config.grid.get_field("ton_based").hidden = 1;
                            frm.fields_dict.custom_customer_traffic_config.grid.get_field("ton_based_sqft").df.label = "Container SQFT";
                        }
                    }
                }
            });
        }
    }
});