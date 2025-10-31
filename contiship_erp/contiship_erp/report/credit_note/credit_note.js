// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.query_reports["Credit Note"] = {
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
    formatter: function (value, row, column, data, default_formatter) {
        if (!data || data.is_total_row) {
            return default_formatter(value, row, column, data);
        }        
        if (column.fieldname === "print_icon" && data.name) {
            return `
                <a href="javascript:void(0)" 
                    onclick="frappe.set_route('print', 'Sales Invoice', '${data.name}')"
                    title="Print Sales Invoice">
                    <i class="fa fa-print" style="cursor:pointer; color:#000;"></i>
                </a>`;
        }    
        if (column.fieldname === "invoiced") {
            if (data.acknowledgement_number && data.acknowledgement_number.trim() !== "") {
                return `<i class="fa fa-check" style="color:#28a745;" title="Consignmented"></i>`;
            } else {
                return `<i class="fa fa-times" style="color:#dc3545;" title="Not Consignmented"></i>`;
            }
        }
        return default_formatter(value, row, column, data);
    }
};