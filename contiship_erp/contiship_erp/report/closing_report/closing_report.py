# Copyright (c) 2025, OneBook and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import formatdate

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Inward Entry ID", "fieldname": "id", "fieldtype": "Link", "options": "Inward Entry", "width": 150},
        {"label": "Consignment", "fieldname": "boeinvoice_no", "fieldtype": "Data", "width": 130},
        {"label": "Arrival Date", "fieldname": "container_arrival_date", "fieldtype": "Date", "width": 110},
        {"label": "Container No", "fieldname": "container", "fieldtype": "Data", "width": 130},
        {"label": "Container Size", "fieldname": "container_size", "fieldtype": "Data", "width": 130},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Grade", "fieldname": "grade", "fieldtype": "Data", "width": 150},
        {"label": "Crossing Item", "fieldname": "crossing_item", "fieldtype": "Data", "width": 100},
        {"label": "Inward Qty", "fieldname": "inward_qty", "fieldtype": "Int", "width": 100},
        {"label": "Outward Qty", "fieldname": "outward_qty", "fieldtype": "Int", "width": 100},
        {"label": "Available Qty", "fieldname": "available_qty", "fieldtype": "Int", "width": 100},
        {"label": "Outward Entry", "fieldname": "outward_entry_id", "fieldtype": "Data", "width": 400},
        {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Data", "width": 400},
    ]
def get_data(filters):
    conditions = ""
    values = {}

    # Date filters
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND ie.arrival_date BETWEEN %(from_date)s AND %(to_date)s"
        values.update({"from_date": filters["from_date"], "to_date": filters["to_date"]})
    elif filters.get("from_date"):
        conditions += " AND ie.arrival_date >= %(from_date)s"
        values.update({"from_date": filters["from_date"]})
    elif filters.get("to_date"):
        conditions += " AND ie.arrival_date <= %(to_date)s"
        values.update({"to_date": filters["to_date"]})

    # Customer filter
    if filters.get("customer"):
        conditions += " AND ie.customer = %(customer)s"
        values["customer"] = filters["customer"]

    # Consignment filter
    if filters.get("consignment"):
        conditions += " AND ie.boeinvoice_no LIKE %(consignment)s"
        values["consignment"] = f"%{filters['consignment']}%"

    # Item filter
    if filters.get("item"):
        conditions += " AND ied.item = %(item)s"
        values["item"] = filters["item"]

    # Fetch only fully outwarded items (available_qty = 0)
    rows = frappe.db.sql(f"""
        SELECT
            ie.name AS id,
            ie.boeinvoice_no,
            ied.container,
            ied.container_size,
            ie.customer,
            ied.item,
            ied.grade,
            ied.container_arrival_date,
            CASE 
                WHEN ied.crossing_item IS NOT NULL AND ied.crossing_item != '' THEN 'Yes'
                ELSE 'No'
            END AS crossing_item,
            CAST(ied.qty AS UNSIGNED) AS inward_qty,
            CAST(IFNULL((
                SELECT SUM(oed.qty)
                FROM `tabOutward Entry Items` AS oed
                JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
                WHERE 
                    oe.consignment = ie.name 
                    AND oed.item = ied.item
                    AND oed.container = ied.name
            ), 0) AS UNSIGNED) AS outward_qty,
            CAST(ied.qty - IFNULL((
                SELECT SUM(oed.qty)
                FROM `tabOutward Entry Items` AS oed
                JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
                WHERE 
                    oe.consignment = ie.name 
                    AND oed.item = ied.item
                    AND oed.container = ied.name
            ), 0) AS UNSIGNED) AS available_qty,
            (
                SELECT GROUP_CONCAT(CONCAT(oe.name, ' (', oed.qty, ')') ORDER BY oe.date DESC SEPARATOR ', ')
                FROM `tabOutward Entry Items` AS oed
                JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
                WHERE 
                    oe.consignment = ie.name 
                    AND oed.item = ied.item
                    AND oed.container = ied.name
            ) AS outward_entry_id,
            (
                SELECT GROUP_CONCAT(CONCAT(si.name) ORDER BY si.posting_date DESC SEPARATOR ', ')
                FROM `tabSales Invoice` AS si
                WHERE si.custom_reference_docname = ie.name
            ) AS sales_invoice
        FROM
            `tabInward Entry` AS ie
        JOIN
            `tabInward Entry Item` AS ied ON ied.parent = ie.name
        WHERE
            1=1 
            {conditions}
            AND CAST(ied.qty - IFNULL((
                SELECT SUM(oed.qty)
                FROM `tabOutward Entry Items` AS oed
                JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
                WHERE 
                    oe.consignment = ie.name 
                    AND oed.item = ied.item
                    AND oed.container = ied.name
            ), 0) AS UNSIGNED) = 0
        ORDER BY
            ie.name DESC
    """, values, as_dict=1)

    # Format outward entries and sales invoice links as before
    for row in rows:
        if row.get("outward_entry_id"):
            entries = []
            for entry in row["outward_entry_id"].split(", "):
                entry_id = entry.split(" ")[0]
                oe_date = frappe.db.get_value("Outward Entry", entry_id, "date")
                if oe_date:
                    oe_date = formatdate(oe_date)
                qty = entry.split("(")[-1].replace(")", "")
                entries.append(f"{oe_date} ({qty})")
            row["outward_entry_id"] = ", ".join(entries)
        else:
            row["outward_entry_id"] = ""

    for row in rows:
        if row.get("sales_invoice"):
            links = []
            for si in row["sales_invoice"].split(","):
                si = si.strip()
                links.append(f'<a href="javascript:void(0)" onclick="frappe.set_route(\'Form\', \'Sales Invoice\', \'{si}\')">{si}</a>')
            row["sales_invoice"] = ", ".join(links)
        else:
            row["sales_invoice"] = ""

    return rows
