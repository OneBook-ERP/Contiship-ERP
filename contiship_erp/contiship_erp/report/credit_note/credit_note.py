# Copyright (c) 2025, OneBook and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Invoice No", "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 250},
        {"label": "Consignment", "fieldname": "custom_consignment", "width": 150},
        {"label": "Taxable Amount", "fieldname": "total", "fieldtype": "Currency", "width": 130},
        {"label": "Total Taxes", "fieldname": "total_taxes_and_charges", "fieldtype": "Currency", "width": 130},
        {"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 130},
        {"label": "Outstanding", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 130},
        {"label": "Status", "fieldname": "status", "width": 120},
        {"label": "Invoice Type", "fieldname": "custom_invoice_type", "width": 140},
        {"label": "Inward Entry", "fieldname": "custom_reference_docname", "fieldtype": "Link", "options": "Inward Entry", "width": 150},
        {"label": "Inward Date", "fieldname": "custom_inward_date", "fieldtype": "Date", "width": 120},
        {"label": "Created On", "fieldname": "creation", "fieldtype": "Date", "width": 140},
    ]

def get_data(filters):
    conditions = ""
    values = {}

    if filters.get("invoice_no"):
        conditions += " AND si.name = %(invoice_no)s"
        values["invoice_no"] = filters["invoice_no"]

    if filters.get("customer"):
        conditions += " AND si.customer = %(customer)s"
        values["customer"] = filters["customer"]

    if filters.get("consignment"):
        conditions += " AND si.custom_consignment = %(consignment)s"
        values["consignment"] = filters["consignment"]

    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s"
        values.update({"from_date": filters["from_date"], "to_date": filters["to_date"]})

    elif filters.get("from_date"):
        conditions += " AND si.posting_date >= %(from_date)s"
        values.update({"from_date": filters["from_date"]})

    elif filters.get("to_date"):
        conditions += " AND si.posting_date <= %(to_date)s"
        values.update({"to_date": filters["to_date"]})


    return frappe.db.sql(f"""
        SELECT
            si.name,
            si.custom_reference_docname,
            si.custom_inward_date,
            si.posting_date,
            si.creation,
            si.customer,
            si.custom_consignment,
            si.total,
            si.total_taxes_and_charges,
            si.grand_total,
            si.outstanding_amount,
            si.status,
            si.custom_invoice_type
        FROM `tabSales Invoice` si
        WHERE si.is_return = 1
        {conditions}
        ORDER BY si.name DESC
    """, values, as_dict=1)
