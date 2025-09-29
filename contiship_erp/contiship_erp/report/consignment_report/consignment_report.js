// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.query_reports["Consignment Report"] = {
	"filters": [
		{
			fieldname: "customer",
			label: "Customer",
			fieldtype: "Link",
			options: "Customer",
			width: 150
		},					
		{
			fieldname: "item",
			label: "Item",
			fieldtype: "Link",
			options: "Item",
			width: 150
		},
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",			
			reqd: 0
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",			
			reqd: 0
		}	
	],

	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "inward_qty") {
			return `<span style="color: green; font-weight: bold;">${value}</span>`;
		}
		if (column.fieldname === "available_qty") {
			return `<span style="color: black; font-weight: bold;">${value}</span>`;
		}
		if (column.fieldname === "outward_qty") {
			return `<span style="color: red; font-weight: bold;">${value}</span>`;
		}

		return value;
	}
};
