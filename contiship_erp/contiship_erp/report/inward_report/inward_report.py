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
		{"label": "Status", "fieldname": "docstatus", "width": 100},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 300},
		{"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": "Quantity", "fieldname": "qty", "fieldtype": "Int", "precision": 0,"width": 100,},
		{"label": "Grade", "fieldname": "grade", "width": 100},
		{"label": "Crossing Item", "fieldname": "crossing_item", "width": 100},
		{"label": "Container", "fieldname": "container", "width": 150},
		{"label": "Container Size", "fieldname": "container_size", "width": 100},
		{"label": "Arrival Date", "fieldname": "arrival_date", "fieldtype": "Date", "width": 110},
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

	elif filters.get("from_date"):
		conditions += " AND ie.arrival_date >= %(from_date)s"
		values.update({"from_date": filters["from_date"]})

	elif filters.get("to_date"):
		conditions += " AND ie.arrival_date <= %(to_date)s"
		values.update({"to_date": filters["to_date"]})

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
			CASE 
				WHEN ie.docstatus = 0 THEN 'Draft'
				WHEN ie.docstatus = 1 THEN 'Submitted'
				WHEN ie.docstatus = 2 THEN 'Cancelled'
			END as docstatus,
			ie.customer,
			ied.item,
			ied.grade,
			ied.container,
			ied.container_size,
			CASE 
				WHEN ied.crossing_item IS NOT NULL AND ied.crossing_item != '' THEN 'Yes'
				ELSE 'No'
			END as crossing_item,
			ie.arrival_date,
			CAST(ied.qty AS UNSIGNED) as qty
		FROM
			`tabInward Entry` ie
		JOIN
			`tabInward Entry Item` ied ON ied.parent = ie.name
		WHERE
			1=1 {conditions}
		ORDER BY
			ie.creation DESC
	""".format(conditions=conditions), values, as_dict=1)
