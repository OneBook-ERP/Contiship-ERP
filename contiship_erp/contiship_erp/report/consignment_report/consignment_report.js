// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.query_reports["Consignment Report"] = {
	"filters": [		
		{
			fieldname: "consignment",
			label: "Consignment",
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Inward Entry', txt);
			},
			default: [],
			width: 150
		},		
		{
			fieldname: "customer",
			label: "Customer",
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Customer', txt);
			},
			default: [],
			width: 150
		},
		
		{
			"fieldname": "item",
			"label": "Item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150
		},
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
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


