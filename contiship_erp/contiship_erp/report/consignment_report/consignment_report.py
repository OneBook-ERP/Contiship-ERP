# Copyright (c) 2025, OneBook and contributors
# For license information, please see license.txt

import frappe

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
        {"label": "Inward Qty", "fieldname": "inward_qty", "fieldtype": "Float", "width": 100},
        {"label": "Available Qty", "fieldname": "available_qty", "fieldtype": "Float", "width": 100},
        {"label": "Outward Qty", "fieldname": "outward_qty", "fieldtype": "Float", "width": 100},
		{"label": "Outward Entry IDs", "fieldname": "outward_entry_id", "fieldtype": "Data", "width": 300},

    ]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND ie.arrival_date BETWEEN %(from_date)s AND %(to_date)s"
		values.update({
			"from_date": filters["from_date"],
			"to_date": filters["to_date"]
		})

	if filters.get("customer"):
		conditions += " AND ie.customer = %(customer)s"
		values["customer"] = filters["customer"]

	if filters.get("item"):
		conditions += " AND ied.item = %(item)s"
		values["item"] = filters["item"]

	if filters.get("consignment"):
		conditions += " AND ie.name = %(consignment)s"
		values["consignment"] = filters["consignment"]

	return frappe.db.sql("""
		SELECT
			ie.name AS id,
			ie.boeinvoice_no,
			ied.container,
			ie.customer,
			ied.item,
			ied.grade,
			ied.container_size,
			ied.container_arrival_date,
			SUM(ied.qty) AS inward_qty,
			IFNULL((
				SELECT SUM(oed.qty)
				FROM `tabOutward Entry Items` AS oed
				JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
				WHERE
					oe.docstatus = 1 AND
					oe.consignment = ie.name AND
					oed.item = ied.item
			), 0) AS outward_qty,
			(SUM(ied.qty) - IFNULL((
				SELECT SUM(oed.qty)
				FROM `tabOutward Entry Items` AS oed
				JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
				WHERE
					oe.docstatus = 1 AND
					oe.consignment = ie.name AND
					oed.item = ied.item
			), 0)) AS available_qty,
			ie.arrival_date,
			(
				SELECT GROUP_CONCAT(DISTINCT oe.name ORDER BY oe.date DESC SEPARATOR ', ')
				FROM `tabOutward Entry Items` AS oed
				JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
				WHERE
					oe.docstatus = 1 AND
					oe.consignment = ie.name AND
					oed.item = ied.item
			) AS outward_entry_id
		FROM
			`tabInward Entry` AS ie
		JOIN
			`tabInward Entry Item` AS ied ON ied.parent = ie.name
		WHERE
			ie.docstatus = 1 {conditions}
		GROUP BY
			ie.name, ied.item
		ORDER BY
			ie.arrival_date DESC
	""".format(conditions=conditions), values, as_dict=1)
