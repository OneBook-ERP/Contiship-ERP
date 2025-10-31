// Copyright (c) 2025, OneBook and contributors
// For license information, please see license.txt

frappe.query_reports["Non GST Invoice"] = {
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
	"onload": function(report) {
       
        let btn = report.page.add_inner_button(__('Add Sales Invoice'), function() {
            frappe.new_doc('Sales Invoice');
        });       
    
        $(btn).css({
            "background-color": "#000",
            "color": "#fff",
            "border-color": "#000"
        });
    },
    formatter: function(value, row, column, data, default_formatter) {
      
        if (column.fieldname === "print_icon") {
            if (data && data.name) {
                return `
                    <a href="javascript:void(0)" 
                        onclick="frappe.set_route('print', 'Sales Invoice', '${data.name}')"
                        title="Print Sales Invoice">
                        <i class="fa fa-print" style="cursor:pointer; color:#000;"></i>
                    </a>`;
            }
            return "";
        }

   
        return default_formatter(value, row, column, data);
    },
};