# Copyright (c) 2025, OneBook and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": "Inward ID", "fieldname": "name", "fieldtype": "Link", "options": "Inward Entry", "width": 150},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 300},
		{"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": "Grade", "fieldname": "grade", "width": 100},
		{"label": "Container", "fieldname": "container", "width": 150},
		{"label": "Container Size", "fieldname": "container_size", "width": 100},
		{"label": "Arrival Date", "fieldname": "arrival_date", "fieldtype": "Date", "width": 110},
		{"label": "Quantity", "fieldname": "qty", "fieldtype": "Float", "width": 100},
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
			ie.name,
			ie.customer,
			ied.item,
			ied.grade,
			ied.container,
			ied.container_size,
			ie.arrival_date,
			ied.qty
		FROM
			`tabInward Entry` ie
		JOIN
			`tabInward Entry Item` ied ON ied.parent = ie.name
		WHERE
			ie.docstatus = 1 {conditions}
		ORDER BY
			ie.arrival_date DESC
	""".format(conditions=conditions), values, as_dict=1)

