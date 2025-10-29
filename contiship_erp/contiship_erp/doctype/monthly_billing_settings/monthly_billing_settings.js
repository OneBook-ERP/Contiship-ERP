// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.ui.form.on("Monthly Billing Settings", {
	create_monthly_billing(frm) {
        console.log(frm.doc.from_start_date)
        frappe.call({
            method: "contiship_erp.custom.traffic_custom.generate_monthly_container_invoices",
            args: {                
                "now": 1,
                "from_start_date": frm.doc.from_start_date
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
    standard_sqft_billing(frm){
        frappe.call({
            method: "contiship_erp.custom.traffic_custom.create_monthly_standard_sqft_invoice",
            args: {                
                "start": 1
            },
            freeze: true,
            freeze_message: "Creating Monthly Standard SQFT Billing...",
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
    additional_sqft_billing(frm){
        frappe.call({
            method: "contiship_erp.custom.traffic_custom.create_monthly_additional_sqft_invoice",
            args: {                
                "end": 1
            },
            freeze: true,
            freeze_message: "Creating Monthly Additional SQFT Billing...",
            callback: function (r) {
                if (r.message) {
                    frappe.show_alert({
                        message: "Monthly Billing created successfully",
                        indicator: "green"
                    });
                }
            }
        });
    }
});
