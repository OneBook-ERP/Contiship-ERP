import frappe
from frappe.model.document import Document
from frappe.utils import getdate
# from contiship_erp.custom.traffic_custom import create_monthly_sales_invoice

class OutwardEntry(Document):

    def validate(self):
        self.calculate_available_space()       

    def on_submit(self):
        # create_monthly_sales_invoice()
        frappe.enqueue("contiship_erp.contiship_erp.doctype.outward_entry.outward_entry.create_sales_invoice", queue='default', job_name=f"Create Sales Invoice for {self.name}", outward_entry=self.name)
   
    def calculate_available_space(self):
        errors = []

        for row in self.items:
            if not (row.container and row.item):
                frappe.throw("Each row must have a container and item.")

            total_inward = frappe.db.sql("""
                SELECT SUM(ii.qty)
                FROM `tabInward Entry Item` ii
                JOIN `tabInward Entry` ie ON ie.name = ii.parent
                WHERE ie.name = %s AND ii.name = %s AND ii.item = %s
            """, (self.consignment, row.container, row.item))[0][0] or 0
            
            used_outward = frappe.db.sql("""
                SELECT SUM(oi.qty)
                FROM `tabOutward Entry Items` oi
                JOIN `tabOutward Entry` o ON o.name = oi.parent
                WHERE o.consignment = %s AND oi.container = %s AND oi.item = %s AND o.name != %s
            """, (self.consignment, row.container, row.item, self.name))[0][0] or 0
            
            available = total_inward - used_outward
            
            if (row.qty or 0) > available:
                errors.append(f"""
                    <b>Container:</b> {row.container}<br>
                    <b>Item:</b> {row.item}<br>
                    <b>Total Inward:</b> {total_inward}<br>
                    <b>Already Outwarded:</b> {used_outward}<br>
                    <b>Currently Requested:</b> {row.qty}<br>
                    <b>Available Remaining:</b> {available}<br><hr>
                """)

        if errors:
            frappe.throw(
                "<b>Outward Entry exceeds available quantity for the following:</b><br><br>" + "".join(errors),
                title="Outward Quantity Exceeded"
            )


@frappe.whitelist()
def get_inward_filter(doctype, txt, searchfield, start, page_len, filters):
    consignment = filters.get("consignment")
    container = filters.get("name")

    if not consignment or not container:
        return []

    items = frappe.db.sql("""
        SELECT DISTINCT iei.item, iei.grade
        FROM `tabInward Entry Item` iei
        JOIN `tabInward Entry` ie ON ie.name = iei.parent
        WHERE ie.name = %(consignment)s
          AND iei.name = %(container)s
          AND iei.item LIKE %(txt)s
        LIMIT %(page_len)s OFFSET %(start)s
    """, {
        "consignment": consignment,
        "container": container,
        "txt": f"%{txt}%",
        "page_len": page_len,
        "start": start
    }, as_dict=1)

    result = []
    for item in items:
        display_text = item["item"] + (f" - {item['grade']}" if item.get("grade") else "")
        result.append([item["item"], display_text])

    return result



@frappe.whitelist()
def get_inward_item_details(consignment, container, item_code):
    if not consignment or not container or not item_code:
        return

    result = frappe.db.sql("""
        SELECT 
            iei.item, iei.qty, iei.uom, iei.grade_item, iei.grade,
            (
                SELECT SUM(oi.qty)
                FROM `tabOutward Entry Items` oi
                JOIN `tabOutward Entry` o ON o.name = oi.parent
                WHERE o.consignment = %(consignment)s
                AND oi.container = %(container)s
                AND oi.item = iei.item
            ) AS used_qty
        FROM `tabInward Entry Item` iei
        JOIN `tabInward Entry` ie ON ie.name = iei.parent
        WHERE ie.name = %(consignment)s
        AND iei.name = %(container)s
        AND iei.item = %(item)s
        LIMIT 1
    """, {
        "consignment": consignment,
        "container": container,
        "item": item_code
    }, as_dict=True)


    if not result:
        return

    row = result[0]
    used = row.used_qty or 0
    remaining_qty = row.qty - used

    if remaining_qty <= 0:
        frappe.throw("No available quantity left for this item.")

    return {
        "qty": remaining_qty,
        "uom": row.uom,       
        "grade_item":row.grade_item,
        "grade":row.grade
    }
   
@frappe.whitelist()
def get_all_inward_items(consignment):
    if not consignment:
        return []

    result = frappe.db.sql("""
        SELECT 
            iei.name as container,
            iei.item,
            iei.qty,
            iei.uom,
            iei.grade_item,
            iei.grade,
            (
                SELECT SUM(oi.qty)
                FROM `tabOutward Entry Items` oi
                JOIN `tabOutward Entry` o ON o.name = oi.parent
                WHERE o.consignment = %(consignment)s
                AND oi.container = iei.name
                AND oi.item = iei.item
            ) AS used_qty
        FROM `tabInward Entry Item` iei
        JOIN `tabInward Entry` ie ON ie.name = iei.parent
        WHERE ie.name = %(consignment)s
    """, {
        "consignment": consignment
    }, as_dict=True)

    items = []
    for row in result:
        used = row.used_qty or 0
        remaining_qty = row.qty - used

        if remaining_qty > 0:
            items.append({
                "container": row.container,
                "item": row.item,
                "qty": remaining_qty,
                "uom": row.uom,
                "grade_item": row.grade_item,
                "grade": row.grade
            })

    return items

    
# @frappe.whitelist()
# def get_inward_items(consignment, name):
#     if not consignment or not name:
#         return

#     entries = frappe.get_all(
#         "Inward Entry",
#         filters={"consignment": consignment, "container": name},
#         fields=["name"]
#     )
#     if not entries:
#         return

#     inward_doc = frappe.get_doc("Inward Entry", entries[0].name)
#     arrival_date = frappe.db.get_value("Container Entry", name, "container_arrival_date")
#     remaining_items = []

#     for item in inward_doc.inward_entry_items:
        
#         used_outward_qty_result = frappe.db.sql("""
#             SELECT SUM(oi.qty)
#             FROM `tabOutward Entry Items` oi
#             JOIN `tabOutward Entry` o ON o.name = oi.parent
#             WHERE o.consignment = %s
#               AND o.container = %s
#               AND oi.item = %s             
#         """, (consignment, name, item.item))

#         used_qty = used_outward_qty_result[0][0] if used_outward_qty_result and used_outward_qty_result[0][0] is not None else 0     

#         remaining_qty = item.qty - used_qty     

#         if remaining_qty > 0:
#             remaining_items.append({
#                 "item": item.item,
#                 "qty": remaining_qty,
#                 "uom": item.uom,
#                 "batch": item.batch
#             })
#         if remaining_qty < 0:
#             frappe.throw("Already completed the outward entry for the container")

#     return {
#         "arrival_date": arrival_date,
#         "inward_items": remaining_items
#     }

# from frappe.utils import getdate

# @frappe.whitelist()
# def create_sales_invoice(outward_entry):
#     frappe.log_error("outward_entry", outward_entry)
#     doc = frappe.get_doc("Outward Entry", outward_entry)
#     consignment = frappe.get_doc("Consignment", doc.consignment)

#     matching_items = []
#     addon_items = []

#     outwards = frappe.get_all("Outward Entry", filters={
#         "consignment": doc.consignment
#     }, pluck="name")

#     for entry in outwards:
#         outward_doc = frappe.get_doc("Outward Entry", entry)
#         addon_items += get_add_on_service_items(outward_doc.add_on_services_outward or [])

#     inwards = frappe.get_all("Inward Entry", filters={
#         "consignment": doc.consignment
#     }, pluck="name")

#     for entry in inwards:
#         frappe.log_error("inward_entry", entry)
#         inward_doc = frappe.get_doc("Inward Entry", entry)
#         addon_items += get_add_on_service_items(inward_doc.add_on_services_inward or [])

#     matching_items.extend(addon_items)
#     frappe.log_error("matching_items", matching_items)

#     if consignment.invoice_generated:
#         frappe.log_error("Invoice already exists", f"{doc.name}")
#         return

#     today = getdate()
#     traffic_config = consignment.customer_traffic_config or []

#     if not traffic_config and consignment.customer:
#         customer = frappe.get_doc("Customer", consignment.customer)
#         traffic_config = customer.customer_traffic_config

#     if not traffic_config:
#         frappe.log_error("Customer Traffic Config not found", f"{doc.name}")
#         return

#     for container in consignment.container_entry:
#         total_inward = frappe.db.sql("""
#             SELECT SUM(ii.qty)
#             FROM `tabInward Entry Item` ii
#             JOIN `tabInward Entry` ie ON ie.name = ii.parent
#             WHERE ie.consignment = %s AND ie.container = %s
#         """, (doc.consignment, container.name))[0][0] or 0

#         used_outward = frappe.db.sql("""
#             SELECT SUM(oi.qty)
#             FROM `tabOutward Entry Items` oi
#             JOIN `tabOutward Entry` o ON o.name = oi.parent
#             WHERE o.consignment = %s AND o.container = %s
#         """, (doc.consignment, container.name))[0][0] or 0

#         if total_inward != used_outward:
#             return

#     item_map = {}

#     for item in consignment.container_entry:
#         arrival_date = getdate(item.container_arrival_date)
#         outward_date = frappe.db.sql("""
#             SELECT MAX(o.date)
#             FROM `tabOutward Entry` o
#             JOIN `tabOutward Entry Items` oi ON oi.parent = o.name
#             WHERE o.consignment = %s AND o.container = %s
#         """, (doc.consignment, item.name))[0][0]

#         if not outward_date:
#             continue

#         outward_date = getdate(outward_date)
#         days_stayed = (outward_date - arrival_date).days or 1

#         total_inward_qty = frappe.db.sql("""
#             SELECT SUM(ii.qty)
#             FROM `tabInward Entry Item` ii
#             JOIN `tabInward Entry` ie ON ii.parent = ie.name
#             WHERE ie.consignment = %s AND ie.container = %s
#         """, (doc.consignment, item.name))[0][0] or 0

#         outward_dates = frappe.db.sql("""
#             SELECT o.date, SUM(oi.qty) AS qty
#             FROM `tabOutward Entry` o
#             JOIN `tabOutward Entry Items` oi ON oi.parent = o.name
#             WHERE o.consignment = %s AND o.container = %s
#             GROUP BY o.date
#             ORDER BY o.date ASC
#         """, (doc.consignment, item.name), as_dict=True)

#         remaining_qty = total_inward_qty
#         threshold_percent = 75
#         threshold_qty = total_inward_qty * (threshold_percent / 100.0)
#         discount_start_date = None
#         for row in outward_dates:
#             remaining_qty -= row.qty or 0
#             if remaining_qty <= threshold_qty:
#                 discount_start_date = getdate(row.date)
#                 break

#         for traffic in traffic_config:
#             service_item = frappe.get_doc("Item", traffic.service_type)
#             enable_75_rule = traffic.enable_75_rule
#             discount_rate = traffic.after_75_discounted_rate or 0

#             if service_item.custom_rent_type == "Container Based":
#                 if item.container_size == service_item.custom_container_feat_size:
#                     apply_discount = False
#                     remaining_qty_temp = total_inward_qty
#                     for row in outward_dates:
#                         remaining_qty_temp -= row.qty or 0
#                         if remaining_qty_temp <= threshold_qty and outward_date == getdate(row.date):
#                             apply_discount = True
#                             break
#                     rate = discount_rate if enable_75_rule and apply_discount else traffic.rate

#                     duration_days = max(days_stayed, traffic.minimum_commitmentnoofdays or 1)
#                     key = f"{traffic.service_type}|{arrival_date}|{outward_date}"

#                     description = f"From {arrival_date.strftime('%d.%m.%y')} to {outward_date.strftime('%d.%m.%y')}<br>"
#                     description += f"{duration_days:02} Days * {rate} = {rate * duration_days}<br>(1*{item.container_size})"

#                     item_map[key] = {
#                         "item_code": traffic.service_type,
#                         "qty": 1,
#                         "uom": "Day",
#                         "rate": rate * duration_days,
#                         "description": description
#                     }

#             elif service_item.custom_rent_type == "Sqft Based":
#                 sqft_min_days = traffic.minimum_commitmentnoofdays or 1
#                 block_size = int(traffic.square_feet_size or 0)
#                 raw_sqft = int(item.container_size or 0) * 10
#                 sqft_used = 500 if raw_sqft <= 500 else 1000 if raw_sqft <= 1000 else raw_sqft
#                 duration_days = max(days_stayed, sqft_min_days)

#                 apply_discount = False
#                 remaining_qty_temp = total_inward_qty
#                 for row in outward_dates:
#                     remaining_qty_temp -= row.qty or 0
#                     if remaining_qty_temp <= threshold_qty and outward_date == getdate(row.date):
#                         apply_discount = True
#                         break

#                 rate = discount_rate if enable_75_rule and apply_discount else traffic.rate
#                 key = f"{traffic.service_type}|{arrival_date}|{outward_date}"

#                 full_blocks = sqft_used // block_size
#                 remaining_sqft = sqft_used % block_size

#                 if full_blocks > 0:
#                     description = f"From {arrival_date.strftime('%d.%m.%y')} to {outward_date.strftime('%d.%m.%y')}<br>"
#                     description += f"{duration_days:02} Days * {rate} = {rate * duration_days}<br>({full_blocks}*{block_size})"
#                     item_map[key] = {
#                         "item_code": traffic.service_type,
#                         "qty": full_blocks,
#                         "uom": "Day",
#                         "rate": rate * duration_days * full_blocks,
#                         "description": description
#                     }

#                 if remaining_sqft > 0:
#                     sqft_500_item_code = traffic.service_type if int(traffic.square_feet_size or 0) == 500 else None
#                     if not sqft_500_item_code:
#                         sqft_500_item = frappe.get_all(
#                             "Item",
#                             filters={"custom_rent_type": "Sqft Based", "custom_square_feet_size": 500},
#                             fields=["name"],
#                             limit=1
#                         )
#                         if sqft_500_item:
#                             sqft_500_item_code = sqft_500_item[0].name

#                     price_data = frappe.db.get_value(
#                         "Item Price",
#                         {"item_code": sqft_500_item_code, "price_list": "Standard Selling", "selling": 1},
#                         ["price_list_rate", "valid_from", "valid_upto"],
#                         as_dict=True
#                     )
#                     rate_500 = price_data.price_list_rate if price_data else 1
#                     if price_data:
#                         valid_from = getdate(price_data.valid_from) if price_data.valid_from else None
#                         valid_upto = getdate(price_data.valid_upto) if price_data.valid_upto else None
#                         if (valid_from and today < valid_from) or (valid_upto and today > valid_upto):
#                             rate_500 = 1

#                     description = f"From {arrival_date.strftime('%d.%m.%y')} to {outward_date.strftime('%d.%m.%y')}<br>"
#                     description += f"{duration_days:02} Days * {rate_500} = {rate_500 * duration_days}<br>(1*{remaining_sqft})"

#                     item_map[key + "_500sqft"] = {
#                         "item_code": sqft_500_item_code,
#                         "qty": 1,
#                         "uom": "Day",
#                         "rate": rate_500 * duration_days,
#                         "description": description
#                     }

#     matching_items.extend([i for i in item_map.values() if i["qty"] > 0])

#     if not matching_items:
#         frappe.log_error("No items for invoice", f"{doc.name}")
#         return

#     invoice = frappe.get_doc({
#         "doctype": "Sales Invoice",
#         "customer": consignment.customer,
#         "posting_date": today,
#         "custom_reference_doctype": "Consignment",
#         "custom_reference_docname": consignment.name,
#         "custom_invoice_type": "Immediate Billing",
#         "items": matching_items
#     })
#     invoice.insert()

#     consignment.invoice_generated = 1
#     consignment.final_invoice_link = invoice.name
#     consignment.save()

# def get_add_on_service_items(add_on_services):
#     items = []
#     for row in add_on_services:
#         frappe.log_error("row", row)
#         if not row.add_on_item or not row.rate:
#             continue
#         items.append({
#             "item_code": row.add_on_item,
#             "item_name": row.service or row.type,
#             "description": f"{row.type} - {row.service}",
#             "qty": row.qty,
#             "rate": row.rate,
#             "uom": "Nos"
#         })
#     return items



@frappe.whitelist()
def create_sales_invoice(outward_entry):
    try:
        # frappe.log_error("outward_entry", outward_entry)
        doc = frappe.get_doc("Outward Entry", outward_entry)

        matching_items = []  
        
        unique_containers = set()
        for item in doc.items:            
            if item.container:
                unique_containers.add(item.container)        
        consignment = frappe.get_doc("Inward Entry", doc.consignment)

        if consignment.invoice_generated:
            frappe.log_error("Invoice already generated for this consignment")

        today = getdate()
        traffic_config = consignment.customer_tariff_config or []
        if not traffic_config and consignment.customer:
            customer = frappe.get_doc("Customer", consignment.customer)
            traffic_config = customer.customer_traffic_config
        if not traffic_config:
            frappe.log_error("Customer Tariff Config not found")

        from collections import defaultdict
        sqft_by_date = defaultdict(list)
        item_map = {}

        for container_id in unique_containers:
            container = frappe.get_doc("Inward Entry Item", container_id)

            total_inward = frappe.db.sql("""
                SELECT SUM(ii.qty) FROM `tabInward Entry Item` ii
                JOIN `tabInward Entry` ie ON ie.name = ii.parent
                WHERE ie.name = %s AND ii.name = %s
            """, (consignment_id, container_id))[0][0] or 0

            used_outward = frappe.db.sql("""
                SELECT SUM(oi.qty) FROM `tabOutward Entry Items` oi
                JOIN `tabOutward Entry` o ON o.name = oi.parent
                WHERE o.consignment = %s AND oi.container = %s
            """, (consignment_id, container_id))[0][0] or 0

            if total_inward != used_outward:
                continue

            outward_date = frappe.db.sql("""
                SELECT MAX(o.date) FROM `tabOutward Entry` o
                JOIN `tabOutward Entry Items` oi ON oi.parent = o.name
                WHERE o.consignment = %s AND oi.container = %s
            """, (consignment_id, container_id))[0][0]

            if not outward_date:
                continue

            arrival_date = getdate(container.container_arrival_date)
            
            last_invoice = frappe.db.sql("""
                SELECT posting_date
                FROM `tabSales Invoice`
                WHERE docstatus = 1
                AND custom_reference_docname = %s
                AND custom_invoice_type = 'Monthly Billing'
                ORDER BY posting_date DESC
                LIMIT 1
            """, (consignment_id,), as_dict=True)

            if last_invoice:
                arrival_date = getdate(last_invoice[0].posting_date)

            outward_date = getdate(outward_date)
            days_stayed = (outward_date - arrival_date).days or 1
            threshold_qty_75 = total_inward * 0.75
            threshold_qty_87_5 = total_inward * 0.875


            outward_dates = frappe.db.sql("""
                SELECT o.date, SUM(oi.qty) AS qty
                FROM `tabOutward Entry` o
                JOIN `tabOutward Entry Items` oi ON oi.parent = o.name
                WHERE o.consignment = %s AND oi.container = %s
                GROUP BY o.date
                ORDER BY o.date ASC
            """, (consignment_id, container_id), as_dict=True)

            apply_75_discount = False
            apply_87_5_discount = False
            remaining_qty = total_inward
            for row in outward_dates:
                remaining_qty -= row.qty or 0
                if outward_date == getdate(row.date):
                    if remaining_qty <= threshold_qty_75:
                        apply_75_discount = True
                    if remaining_qty <= threshold_qty_87_5:
                        apply_87_5_discount = True


            raw_sqft = int(container.container_size or 0) * 10

            for traffic in traffic_config:
                service_item = frappe.get_doc("Item", traffic.service_type)

                if not hasattr(service_item, 'custom_rent_type'):
                    continue

                duration = max(days_stayed, traffic.minimum_commitmentnoofdays or 1)
                if traffic.enable_75_rule and apply_75_discount:
                    rate = traffic.after_75_discounted_rate
                elif traffic.enable_875_rule and apply_87_5_discount:
                    rate = traffic.after_875discounted_rate
                else:
                    rate = traffic.rate


                if service_item.custom_rent_type == "Container Based":
                    if str(container.container_size) == str(service_item.custom_container_feat_size):
                        key = f"{traffic.service_type}|{arrival_date}|{outward_date}|container"
                        item_map[key] = {
                            "item_code": traffic.service_type,
                            "qty": 1,
                            "uom": "Day",
                            "rate": rate * duration,
                            "description": (
                                f"From {arrival_date.strftime('%d.%m.%y')} to {outward_date.strftime('%d.%m.%y')}<br>"
                                f"{duration} Days * {rate} = {rate * duration}<br>"
                                f"(1*{container.container_size})"
                            )
                        }

                elif service_item.custom_rent_type == "Sqft Based":
                    sqft_by_date[outward_date].append({
                        "sqft": raw_sqft,
                        "arrival_date": arrival_date,
                        "days_stayed": days_stayed,
                        "container_id": container_id
                    })

        for outward_date, containers in sqft_by_date.items():
            total_sqft = sum(c["sqft"] for c in containers)
            arrival_date = containers[0]["arrival_date"]
            min_days = min(c["days_stayed"] for c in containers)

            sqft_configs = sorted(
                [tc for tc in traffic_config if frappe.get_value("Item", tc.service_type, "custom_rent_type") == "Sqft Based"],
                key=lambda x: int(x.square_feet_size or 0),
                reverse=True
            )

            remaining_sqft = total_sqft

            for config in sqft_configs:
                block_size = int(config.square_feet_size or 0)
                if block_size <= 0: continue

                block_count = remaining_sqft // block_size
                if block_count == 0: continue

                remaining_sqft -= block_count * block_size
                duration = max(min_days, config.minimum_commitmentnoofdays or 1)
                if config.enable_75_rule and apply_75_discount:
                    rate = config.after_75_discounted_rate
                elif config.enable_875_rule and apply_87_5_discount:
                    rate = config.after_875discounted_rate
                else:
                    rate = config.rate

                key = f"{config.service_type}|{arrival_date}|{outward_date}|{block_size}"
                item_map[key] = {
                    "item_code": config.service_type,
                    "qty": block_count,
                    "uom": "Day",
                    "rate": rate * duration * block_count,
                    "description": (
                        f"From {arrival_date.strftime('%d.%m.%y')} to {outward_date.strftime('%d.%m.%y')}<br>"
                        f"{duration} Days * {rate} = {rate * duration}<br>"
                        f"({block_count}*{round(block_size/10)})"
                    )
                }

            if remaining_sqft > 0:
                config_500 = next((cfg for cfg in sqft_configs if cfg.square_feet_size == 500), None)
                if config_500:
                    duration = max(min_days, config_500.minimum_commitmentnoofdays or 1)
                    if config_500.enable_75_rule and apply_75_discount:
                        rate_500 = config_500.after_75_discounted_rate
                    elif config_500.enable_875_rule and apply_87_5_discount:
                        rate_500 = config_500.after_875discounted_rate
                    else:
                        rate_500 = config_500.rate

                    key = f"{config_500.service_type}|{arrival_date}|{end_date}|500"
                    item_map[key] = {
                        "item_code": config_500.service_type,
                        "qty": 1,
                        "uom": "Day",
                        "rate": rate_500 * duration,
                        "description": (
                            f"From {arrival_date.strftime('%d.%m.%y')} to {end_date.strftime('%d.%m.%y')}<br>"
                            f"{duration} Days * {rate_500} = {rate_500 * duration}<br>"
                            f"(1*{round(remaining_sqft/10)})"
                        )
                    }


        matching_items.extend([i for i in item_map.values() if i["qty"] > 0])

        if not matching_items:
            frappe.throw("No invoice items found")

        invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": consignment.customer,
            "posting_date": today,
            "custom_reference_doctype": "Inward Entry",
            "custom_reference_docname": consignment.name,
            "custom_invoice_type": "Immediate Billing",
            "items": matching_items
        })
        invoice.insert()

        consignment.invoice_generated = 1
        # consignment.sales_invoice = invoice.name
        consignment.save()

        return invoice.name

    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Failed to create invoice for outward entry {outward_entry}")
