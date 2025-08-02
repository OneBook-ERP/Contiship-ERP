# Copyright (c) 2025, OneBook and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InwardEntry(Document):

    # def validate(self):        
    #     inward_total_qty = sum(row.qty or 0 for row in self.inward_entry_items)
    #     addon_total_qty = sum(row.qty or 0 for row in self.add_on_services_inward)

    #     if addon_total_qty > inward_total_qty:
    #         frappe.throw(f"Total quantity mismatch: Inward Entry Items = {inward_total_qty}, Add-on Services = {addon_total_qty}")

    def on_submit(self):
        if self.add_on_services_inward:
            frappe.enqueue("contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.create_sales_invoice", queue='default', job_name=f"Create Sales Invoice for {self.name}", inward_entry=self.name)

@frappe.whitelist()
def create_sales_invoice(inward_entry):
    inward_entry = frappe.get_doc("Inward Entry", inward_entry)

    if not inward_entry.add_on_services_inward:
        frappe.throw("No Add-on items found in this Inward Entry.")

    sales_invoice = frappe.new_doc("Sales Invoice")
    sales_invoice.customer = inward_entry.customer
    sales_invoice.custom_reference_doctype = "Inward Entry"
    sales_invoice.custom_reference_docname = inward_entry.name
    sales_invoice.custom_invoice_type = "Add-on Billing"
    sales_invoice.custom_consignment = inward_entry.boeinvoice_no

    for row in inward_entry.add_on_services_inward:
        if not row.add_on_item:
            continue

        sales_invoice.append("items", {
            "item_code": row.add_on_item,
            "qty": row.qty or 1,            
            "rate": row.rate,
            "description": "",
            "uom": row.uom or "Nos"           
        })

    if not sales_invoice.items:
        frappe.throw("No valid Add-on items to invoice.")

    sales_invoice.save()
    # sales_invoice.submit()

    return sales_invoice.name


@frappe.whitelist()
def get_containers(doctype, txt, searchfield, start, page_len, filters):
    """Return containers for the selected consignment with display text as 'ConsignmentID - Item Name'"""
    consignment = filters.get('consignment')
    exclude = filters.get("exclude", [])
    if not consignment:
        return []   

    containers = frappe.db.sql("""
        SELECT ce.name, ce.container, ce.item, ce.grade
        FROM `tabInward Entry Item` ce        
        WHERE ce.parent = %(consignment)s AND ce.name NOT IN %(exclude)s
    """, {'consignment': consignment,"exclude": tuple(exclude) if exclude else ('',)}, as_dict=1)

    result = []
    for container in containers:
        display_text = f"{consignment} - {container.container}"
        result.append([container.name, display_text])
    
    return result

@frappe.whitelist()
def get_traffic_config(customer):
    return frappe.get_doc("Customer", customer)

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


@frappe.whitelist()
def get_items_rate(item):
    from frappe.utils import getdate, nowdate    
    today = getdate(nowdate())

    price_data = frappe.db.get_value(
        "Item Price",
        {
            "item_code": item,
            "price_list": "Standard Selling",
            "selling": 1
        },
        ["price_list_rate", "valid_from", "valid_upto"],
        as_dict=True
    )
    if not price_data:
        return {
            "price": 0
        }

    valid_from = getdate(price_data.valid_from) if price_data.valid_from else None
    valid_upto = getdate(price_data.valid_upto) if price_data.valid_upto else None

    if (valid_from and today < valid_from) or (valid_upto and today > valid_upto):
        return {
            "price": 0
        }

    return {
        "price": price_data.price_list_rate or 0
    }

