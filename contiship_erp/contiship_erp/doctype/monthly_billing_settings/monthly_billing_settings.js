// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.ui.form.on("Monthly Billing Settings", {
	create_monthly_billing(frm) {
        frappe.call({
            method: "contiship_erp.custom.traffic_custom.create_monthly_sales_invoice",
            args: {                
                "monthly_invoice_generated": 1
            },
            freeze: true,
            freeze_message: "Creating Monthly Billing...",
            callback: function (r) {
                if (r.message) {
                    frappe.show_alert({
                        message: "Monthly Billing created successfully",
                        indicator: "green"
                    });
                }
            }
        });

	},
});
