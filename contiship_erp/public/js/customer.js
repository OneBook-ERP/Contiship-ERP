frappe.ui.form.on("Customer",{

    
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
                        frappe.model.set_value(cdt, cdn, "container_sqft", r.message.container_feet);
                        frappe.model.set_value(cdt, cdn, "minimum_commitmentnoofdays", r.message.min_commitment);
                        frm.refresh_field("custom_customer_traffic_config");
                    }
                }
            });
        }
    }
});