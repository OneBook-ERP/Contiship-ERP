# Copyright (c) 2025, OneBook and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import formatdate



class InwardEntry(Document):

    # def validate(self):
        
    
    def on_submit(self):
        self.validate_services()
        self.set_invoice_date()
        if self.add_on_services_inward:
            frappe.enqueue("contiship_erp.contiship_erp.doctype.inward_entry.inward_entry.create_sales_invoice", queue='default', job_name=f"Create Sales Invoice for {self.name}", inward_entry=self.name)

    def validate_services(self):
        if self.service_type == "Sqft Based":
            if not any(t.rent_type == "Sqft Based" for t in self.customer_tariff_config):
                frappe.throw("Sqft Based tariff is not set for this Inward Entry tariff.")

        else:
            if self.inward_entry_items:
                for item in self.inward_entry_items:
                    if not item.rate:
                        frappe.throw(f"Rate is not set for this Inward Entry item. Container: <b>{item.container}</b> arrival at {formatdate(item.container_arrival_date)}")

                    if not item.service_type:
                        frappe.throw(f"Tariff Service is not set for this Inward Entry item. Container: <b>{item.container}</b> arrival at {formatdate(item.container_arrival_date)}")

            # for items in self.inward_entry_items:
            #     if items.container_size == "20" and not items.rate:
            #         if not any(t.rent_type == "Container Based" and t.container_feet == 20 for t in self.customer_tariff_config):
            #             frappe.throw("20 Ft Container Based tariff is not set for this Inward Entry tariff.")
            #     elif items.container_size == "40" and not items.rate:
            #         if not any(t.rent_type == "Container Based" and t.container_feet == 40 for t in self.customer_tariff_config):
            #             frappe.throw("40 Ft Container Based tariff is not set for this Inward Entry tariff.")
            #     elif items.container_size == "LCL" and not items.rate:
            #         if not any(t.rent_type == "LCL" for t in self.customer_tariff_config):
            #             frappe.throw("LCL Based tariff is not set for this Inward Entry tariff.")


    def set_invoice_date(self):
        if self.inward_entry_items:
            self.sales_invoice_inward_date = self.inward_entry_items[0].container_arrival_date
            self.save()
            frappe.db.commit()

                    

@frappe.whitelist()
def create_sales_invoice(inward_entry):
    inward_entry = frappe.get_doc("Inward Entry", inward_entry)

    if not inward_entry.add_on_services_inward:
        frappe.throw("No Add-on items found in this Inward Entry.")

    sales_invoice = frappe.new_doc("Sales Invoice")
    sales_invoice.customer = inward_entry.customer
    sales_invoice.custom_reference_doctype = "Inward Entry"
    sales_invoice.custom_reference_docname = inward_entry.name
    sales_invoice.custom_invoice_type = "Handling"
    sales_invoice.custom_consignment = inward_entry.boeinvoice_no
    sales_invoice.custom_inward_date = inward_entry.arrival_date

    for row in inward_entry.add_on_services_inward:
        if not row.add_on_item:
            continue

        sales_invoice.append("items", {
            "item_code": row.add_on_item,
            "qty": row.qty or 1,            
            "rate": row.rate,
            "description": row.description or "",
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
def get_items_rate(item,tariffs):
    from frappe.utils import getdate, nowdate
    import json  
    today = getdate(nowdate())

    if tariffs:
        if isinstance(tariffs, str):
            tariffs = json.loads(tariffs)

        for tariff in tariffs:
            if tariff.get("service_type") == item:
                return {
                    "price": tariff.get("rate", 0)
                }

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


    
