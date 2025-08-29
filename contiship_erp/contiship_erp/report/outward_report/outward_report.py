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
		{"label": "Status", "fieldname": "docstatus", "width": 100},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 300},
		{"label": "Inward ID", "fieldname": "consignment", "fieldtype": "Link", "options": "Inward Entry", "width": 150},
		{"label": "Consignment", "fieldname": "boeinvoice_no", "fieldtype": "Link", "options": "Inward Entry", "width": 200},
		{"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": "Grade", "fieldname": "grade", "width": 100},
		{"label": "Crossing Item", "fieldname": "crossing_item", "width": 100},
		{"label": "Container", "fieldname": "container", "fieldtype": "Data", "width": 120},
		{"label": "Total Inward Qty", "fieldname": "inward_qty", "fieldtype": "Int", "width": 120},
		{"label": "Available Qty", "fieldname": "available_qty", "fieldtype": "Int", "width": 120},
		{"label": "Total Outward Qty", "fieldname": "qty", "fieldtype": "Int", "width": 100},
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
			CASE 
				WHEN oe.docstatus = 0 THEN 'Draft'
				WHEN oe.docstatus = 1 THEN 'Submitted'
				WHEN oe.docstatus = 2 THEN 'Cancelled'
			END AS docstatus,
			CASE 
				WHEN oed.crossing_item IS NOT NULL AND oed.crossing_item != '' THEN 'Yes'
				ELSE 'No'
			END as crossing_item,
			oe.customer,
			oe.boeinvoice_no,
			oe.consignment,
			oed.item,
			oed.grade,
			ied.container,   -- 🔹 Get container from Inward Entry Item
			CAST(oed.qty AS UNSIGNED) AS qty,
			CAST((
				SELECT SUM(ied2.qty)
				FROM `tabInward Entry Item` ied2
				JOIN `tabInward Entry` ie2 ON ie2.name = ied2.parent
				WHERE
					ie2.name = oe.consignment
					AND ied2.item = oed.item
			) AS UNSIGNED) AS inward_qty,
			CAST((
				COALESCE((
					SELECT SUM(ied3.qty)
					FROM `tabInward Entry Item` ied3
					JOIN `tabInward Entry` ie3 ON ie3.name = ied3.parent
					WHERE
						ie3.name = oe.consignment
						AND ied3.item = oed.item
				), 0) -
				COALESCE((
					SELECT SUM(oed2.qty)
					FROM `tabOutward Entry Items` oed2
					JOIN `tabOutward Entry` oe2 ON oe2.name = oed2.parent
					WHERE
						oe2.boeinvoice_no = oe.boeinvoice_no
						AND oed2.item = oed.item
						AND oe2.docstatus = 1
				), 0)
			) AS UNSIGNED) AS available_qty,
			oe.date
		FROM
			`tabOutward Entry` oe
		JOIN
			`tabOutward Entry Items` oed ON oed.parent = oe.name
		LEFT JOIN
			`tabInward Entry Item` ied ON ied.parent = oe.consignment AND ied.item = oed.item
		WHERE
			1=1 {conditions}
		ORDER BY
			oe.date DESC
""".format(conditions=conditions), values, as_dict=1)
