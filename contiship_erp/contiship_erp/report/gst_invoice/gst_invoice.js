// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.query_reports["GST Invoice"] = {
    "filters": [
		{
            "fieldname": "invoice_no",
            "label": "Invoice No",
            "fieldtype": "Data",
        },
        {
            "fieldname": "customer",
            "label": "Customer",
            "fieldtype": "Link",
            "options": "Customer"
        },
		{
            "fieldname": "consignment",
            "label": "Consignment",
            "fieldtype": "Data",
        },
		{
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
        },
		{
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
        },       
    ],	
};
