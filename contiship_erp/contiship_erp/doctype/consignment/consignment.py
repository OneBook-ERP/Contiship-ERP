# Copyright (c) 2025, OneBook and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Consignment(Document):
	pass



@frappe.whitelist()
def get_traffic_config(customer):
    return frappe.get_doc("Customer", customer)
