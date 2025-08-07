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
	],
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
	
		if (column.fieldname === "docstatus") {
			if (value === "Submitted") {
				return `<span style="background-color: #cce5ff; color: #004085; font-weight: bold; padding: 2px 6px; border-radius: 4px;">${value}</span>`;
			}
			if (value === "Draft") {
				return `<span style="background-color: #ffcccc; color: #721c24; font-weight: bold; padding: 2px 6px; border-radius: 4px;">${value}</span>`;
			}
			if (value === "Cancelled") {
				return `<span style="background-color: #f8d7da; color: #721c24; font-weight: bold; padding: 2px 6px; border-radius: 4px;">${value}</span>`;
			}
		}
		if (column.fieldname === "qty") {
			return `<span style="color: green; font-weight: bold;">${value}</span>`;
		}
	
		return value;
	}
	
};

