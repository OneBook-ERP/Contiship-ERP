// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.query_reports["Inward Report"] = {
	"filters": [
		{
			fieldname: "customer",
			label: "Customer",
			fieldtype: "Link",
			options: "Customer"
		},
		{
			fieldname: "consignment",
			label: "Consignment",
			fieldtype: "Link",
			options: "Inward Entry",
			get_query: () => {
				let customer = frappe.query_report.get_filter_value("customer");
				if (customer) {
					return {
						filters: {
							customer: customer
						}
					};
				}
			}
		},
		{
			fieldname: "item",
			label: "Item",
			fieldtype: "Link",
			options: "Item"
		},
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		}
	]
};

