import frappe
from frappe.model.document import Document

class OutwardEntry(Document):

    def validate(self):
        self.calculate_available_space()       

    def on_submit(self):
        frappe.enqueue("contiship_erp.contiship_erp.doctype.outward_entry.outward_entry.create_sales_invoice", queue='default', job_name=f"Create Sales Invoice for {self.name}", outward_entry=self.name)
   
    def calculate_available_space(self):
        current_outward_total = sum(row.qty for row in self.items)

        total_inward_result = frappe.db.sql("""
            SELECT SUM(ii.qty)
            FROM `tabInward Entry Item` ii
            JOIN `tabInward Entry` ie ON ie.name = ii.parent
            WHERE ie.consignment = %s AND ie.container = %s
        """, (self.consignment, self.container))

        total_inward = total_inward_result[0][0] if total_inward_result and total_inward_result[0][0] is not None else 0

        used_outward_result = frappe.db.sql("""
            SELECT SUM(oi.qty)
            FROM `tabOutward Entry Items` oi
            JOIN `tabOutward Entry` o ON o.name = oi.parent
            WHERE o.consignment = %s AND o.container = %s AND o.name != %s
        """, (self.consignment, self.container, self.name))

        used_outward = used_outward_result[0][0] if used_outward_result and used_outward_result[0][0] is not None else 0

        available = total_inward - used_outward

        if current_outward_total > available:
            frappe.throw(f"""
                <b>Outward Entry exceeds available quantity for container</b><br><br>
                <b>Total Inward:</b> {total_inward}<br>
                <b>Already Outwarded:</b> {used_outward}<br>
                <b>Currently Requested:</b> {current_outward_total}<br>
                <b>Available Remaining:</b> {available}<br><br>
                Please reduce the quantity or choose a different container.
            """, title="Outward Quantity Exceeded")
        
        return {
            "current_outward_total": current_outward_total,
            "available": available
        }

@frappe.whitelist()
def get_inward_items(consignment, name):
    if not consignment or not name:
        return

    entries = frappe.get_all(
        "Inward Entry",
        filters={"consignment": consignment, "container": name},
        fields=["name"]
    )
    if not entries:
        return

    inward_doc = frappe.get_doc("Inward Entry", entries[0].name)
    arrival_date = frappe.db.get_value("Container Entry", name, "container_arrival_date")
    remaining_items = []

    for item in inward_doc.inward_entry_items:
        
        used_outward_qty_result = frappe.db.sql("""
            SELECT SUM(oi.qty)
            FROM `tabOutward Entry Items` oi
            JOIN `tabOutward Entry` o ON o.name = oi.parent
            WHERE o.consignment = %s
              AND o.container = %s
              AND oi.item = %s             
        """, (consignment, name, item.item))

        used_qty = used_outward_qty_result[0][0] if used_outward_qty_result and used_outward_qty_result[0][0] is not None else 0     

        remaining_qty = item.qty - used_qty     

        if remaining_qty > 0:
            remaining_items.append({
                "item": item.item,
                "qty": remaining_qty,
                "uom": item.uom,
                "batch": item.batch
            })
        if remaining_qty < 0:
            frappe.throw("Already completed the outward entry for the container")

    return {
        "arrival_date": arrival_date,
        "inward_items": remaining_items
    }

from frappe.utils import getdate

@frappe.whitelist()
def create_sales_invoice(outward_entry):
    frappe.log_error("outward_entry", outward_entry)
    doc = frappe.get_doc("Outward Entry", outward_entry)
    consignment = frappe.get_doc("Consignment", doc.consignment)

    matching_items = []
    addon_items = []

    outwards = frappe.get_all("Outward Entry", filters={
        "consignment": doc.consignment
    }, pluck="name")

    for entry in outwards:
        outward_doc = frappe.get_doc("Outward Entry", entry)
        addon_items += get_add_on_service_items(outward_doc.add_on_services_outward or [])

    inwards = frappe.get_all("Inward Entry", filters={
        "consignment": doc.consignment
    }, pluck="name")

    for entry in inwards:
        frappe.log_error("inward_entry", entry)
        inward_doc = frappe.get_doc("Inward Entry", entry)
        addon_items += get_add_on_service_items(inward_doc.add_on_services_inward or [])

    matching_items.extend(addon_items)
    frappe.log_error("matching_items", matching_items)

    if consignment.invoice_generated:
        frappe.log_error("Invoice already exists", f"{doc.name}")
        return

    today = getdate()
    traffic_config = consignment.customer_traffic_config or []

    if not traffic_config and consignment.customer:
        customer = frappe.get_doc("Customer", consignment.customer)
        traffic_config = customer.customer_traffic_config

    if not traffic_config:
        frappe.log_error("Customer Traffic Config not found", f"{doc.name}")
        return

    for container in consignment.container_entry:
        total_inward = frappe.db.sql("""
            SELECT SUM(ii.qty)
            FROM `tabInward Entry Item` ii
            JOIN `tabInward Entry` ie ON ie.name = ii.parent
            WHERE ie.consignment = %s AND ie.container = %s
        """, (doc.consignment, container.name))[0][0] or 0

        used_outward = frappe.db.sql("""
            SELECT SUM(oi.qty)
            FROM `tabOutward Entry Items` oi
            JOIN `tabOutward Entry` o ON o.name = oi.parent
            WHERE o.consignment = %s AND o.container = %s
        """, (doc.consignment, container.name))[0][0] or 0

        if total_inward != used_outward:
            return

    item_map = {}

    for item in consignment.container_entry:
        arrival_date = getdate(item.container_arrival_date)
        outward_date = frappe.db.sql("""
            SELECT MAX(o.date)
            FROM `tabOutward Entry` o
            JOIN `tabOutward Entry Items` oi ON oi.parent = o.name
            WHERE o.consignment = %s AND o.container = %s
        """, (doc.consignment, item.name))[0][0]

        if not outward_date:
            continue

        outward_date = getdate(outward_date)
        days_stayed = (outward_date - arrival_date).days or 1

        total_inward_qty = frappe.db.sql("""
            SELECT SUM(ii.qty)
            FROM `tabInward Entry Item` ii
            JOIN `tabInward Entry` ie ON ii.parent = ie.name
            WHERE ie.consignment = %s AND ie.container = %s
        """, (doc.consignment, item.name))[0][0] or 0

        outward_dates = frappe.db.sql("""
            SELECT o.date, SUM(oi.qty) AS qty
            FROM `tabOutward Entry` o
            JOIN `tabOutward Entry Items` oi ON oi.parent = o.name
            WHERE o.consignment = %s AND o.container = %s
            GROUP BY o.date
            ORDER BY o.date ASC
        """, (doc.consignment, item.name), as_dict=True)

        remaining_qty = total_inward_qty
        threshold_percent = 75
        threshold_qty = total_inward_qty * (threshold_percent / 100.0)
        discount_start_date = None
        for row in outward_dates:
            remaining_qty -= row.qty or 0
            if remaining_qty <= threshold_qty:
                discount_start_date = getdate(row.date)
                break

        for traffic in traffic_config:
            service_item = frappe.get_doc("Item", traffic.service_type)
            enable_75_rule = traffic.enable_75_rule
            discount_rate = traffic.after_75_discounted_rate or 0

            if service_item.custom_rent_type == "Container Based":
                if item.container_size == service_item.custom_container_feat_size:
                    apply_discount = False
                    remaining_qty_temp = total_inward_qty
                    for row in outward_dates:
                        remaining_qty_temp -= row.qty or 0
                        if remaining_qty_temp <= threshold_qty and outward_date == getdate(row.date):
                            apply_discount = True
                            break
                    rate = discount_rate if enable_75_rule and apply_discount else traffic.rate

                    duration_days = max(days_stayed, traffic.minimum_commitmentnoofdays or 1)
                    key = f"{traffic.service_type}|{arrival_date}|{outward_date}"

                    description = f"From {arrival_date.strftime('%d.%m.%y')} to {outward_date.strftime('%d.%m.%y')}<br>"
                    description += f"{duration_days:02} Days * {rate} = {rate * duration_days}<br>(1*{item.container_size})"

                    item_map[key] = {
                        "item_code": traffic.service_type,
                        "qty": 1,
                        "uom": "Day",
                        "rate": rate * duration_days,
                        "description": description
                    }

            elif service_item.custom_rent_type == "Sqft Based":
                sqft_min_days = traffic.minimum_commitmentnoofdays or 1
                block_size = int(traffic.square_feet_size or 0)
                raw_sqft = int(item.container_size or 0) * 10
                sqft_used = 500 if raw_sqft <= 500 else 1000 if raw_sqft <= 1000 else raw_sqft
                duration_days = max(days_stayed, sqft_min_days)

                apply_discount = False
                remaining_qty_temp = total_inward_qty
                for row in outward_dates:
                    remaining_qty_temp -= row.qty or 0
                    if remaining_qty_temp <= threshold_qty and outward_date == getdate(row.date):
                        apply_discount = True
                        break

                rate = discount_rate if enable_75_rule and apply_discount else traffic.rate
                key = f"{traffic.service_type}|{arrival_date}|{outward_date}"

                full_blocks = sqft_used // block_size
                remaining_sqft = sqft_used % block_size

                if full_blocks > 0:
                    description = f"From {arrival_date.strftime('%d.%m.%y')} to {outward_date.strftime('%d.%m.%y')}<br>"
                    description += f"{duration_days:02} Days * {rate} = {rate * duration_days}<br>({full_blocks}*{block_size})"
                    item_map[key] = {
                        "item_code": traffic.service_type,
                        "qty": full_blocks,
                        "uom": "Day",
                        "rate": rate * duration_days * full_blocks,
                        "description": description
                    }

                if remaining_sqft > 0:
                    sqft_500_item_code = traffic.service_type if int(traffic.square_feet_size or 0) == 500 else None
                    if not sqft_500_item_code:
                        sqft_500_item = frappe.get_all(
                            "Item",
                            filters={"custom_rent_type": "Sqft Based", "custom_square_feet_size": 500},
                            fields=["name"],
                            limit=1
                        )
                        if sqft_500_item:
                            sqft_500_item_code = sqft_500_item[0].name

                    price_data = frappe.db.get_value(
                        "Item Price",
                        {"item_code": sqft_500_item_code, "price_list": "Standard Selling", "selling": 1},
                        ["price_list_rate", "valid_from", "valid_upto"],
                        as_dict=True
                    )
                    rate_500 = price_data.price_list_rate if price_data else 1
                    if price_data:
                        valid_from = getdate(price_data.valid_from) if price_data.valid_from else None
                        valid_upto = getdate(price_data.valid_upto) if price_data.valid_upto else None
                        if (valid_from and today < valid_from) or (valid_upto and today > valid_upto):
                            rate_500 = 1

                    description = f"From {arrival_date.strftime('%d.%m.%y')} to {outward_date.strftime('%d.%m.%y')}<br>"
                    description += f"{duration_days:02} Days * {rate_500} = {rate_500 * duration_days}<br>(1*{remaining_sqft})"

                    item_map[key + "_500sqft"] = {
                        "item_code": sqft_500_item_code,
                        "qty": 1,
                        "uom": "Day",
                        "rate": rate_500 * duration_days,
                        "description": description
                    }

    matching_items.extend([i for i in item_map.values() if i["qty"] > 0])

    if not matching_items:
        frappe.log_error("No items for invoice", f"{doc.name}")
        return

    invoice = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": consignment.customer,
        "posting_date": today,
        "custom_reference_doctype": "Consignment",
        "custom_reference_docname": consignment.name,
        "custom_invoice_type": "Immediate Billing",
        "items": matching_items
    })
    invoice.insert()

    consignment.invoice_generated = 1
    consignment.final_invoice_link = invoice.name
    consignment.save()

def get_add_on_service_items(add_on_services):
    items = []
    for row in add_on_services:
        frappe.log_error("row", row)
        if not row.add_on_item or not row.rate:
            continue
        items.append({
            "item_code": row.add_on_item,
            "item_name": row.service or row.type,
            "description": f"{row.type} - {row.service}",
            "qty": row.qty,
            "rate": row.rate,
            "uom": "Nos"
        })
    return items
