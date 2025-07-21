# Copyright (c) 2025, OneBook and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": "Outward ID", "fieldname": "name", "fieldtype": "Link", "options": "Outward Entry", "width": 150},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 300},
		{"label": "Inward ID", "fieldname": "consignment", "fieldtype": "Link", "options": "Inward Entry", "width": 150},
		{"label": "Consignment", "fieldname": "boeinvoice_no", "fieldtype": "Link", "options": "Inward Entry", "width": 200},
		{"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": "Grade", "fieldname": "grade", "width": 100},
		{"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 100},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100}
	]

def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND oe.date BETWEEN %(from_date)s AND %(to_date)s"
		values.update({
			"from_date": filters["from_date"],
			"to_date": filters["to_date"]
		})

	if filters.get("customer"):
		conditions += " AND oe.customer = %(customer)s"
		values["customer"] = filters["customer"]

	if filters.get("item"):
		conditions += " AND oed.item = %(item)s"
		values["item"] = filters["item"]

	if filters.get("consignment"):
		conditions += " AND oe.boeinvoice_no = %(consignment)s"
		values["consignment"] = filters["consignment"]

	return frappe.db.sql("""
		SELECT
			oe.name,
			oe.customer,
			oe.boeinvoice_no,
			oe.consignment,
			oed.item,
			oed.grade,
			oed.qty,
			oe.date
		FROM
			`tabOutward Entry` oe
		JOIN
			`tabOutward Entry Items` oed ON oed.parent = oe.name
		WHERE
			oe.docstatus = 1 {conditions}
		ORDER BY
			oe.date DESC
	""".format(conditions=conditions), values, as_dict=1)
