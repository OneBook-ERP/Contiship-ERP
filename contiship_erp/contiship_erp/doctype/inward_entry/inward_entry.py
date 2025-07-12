# Copyright (c) 2025, OneBook and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InwardEntry(Document):
    pass

@frappe.whitelist()
def get_containers(doctype, txt, searchfield, start, page_len, filters):
    """Return containers for the selected consignment with display text as 'ConsignmentID - Item Name'"""
    consignment = filters.get('consignment')
    if not consignment:
        return []
    
    # Get all container entries for this consignment with item details
    containers = frappe.db.sql("""
        SELECT ce.name, ce.containers, i.item_name 
        FROM `tabContainer Entry` ce
        LEFT JOIN `tabItem` i ON ce.containers = i.name
        WHERE ce.parent = %(consignment)s
    """, {'consignment': consignment}, as_dict=1)
    
    # Format as [value, description] where description is 'ConsignmentID - Item Name'
    result = []
    for container in containers:
        display_text = f"{consignment} - {container.item_name or container.containers}"
        result.append([container.name, display_text])
    
    return result

@frappe.whitelist()
def get_container_details(container_id):
    """Get container details including the linked item code and name"""
    if not container_id:
        return {}
    
    container = frappe.get_doc('Container Entry', container_id)
    item_details = frappe.db.get_value('Item', container.containers, 
                                     ['item_name', 'item_code'], as_dict=1) or {}
    
    return {
        'item_code': container.containers,
        'item_name': item_details.get('item_name', container.containers),
        'consignment': container.parent
    }

@frappe.whitelist()
def get_arrival_date(name):
    arrival_date = frappe.db.get_value("Container Entry", name, "container_arrival_date")
    return arrival_date
