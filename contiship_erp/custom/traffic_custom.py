import frappe
from frappe.utils import nowdate

@frappe.whitelist()
def fetch_item_data(service_type):
    try:
        item = frappe.get_doc("Item", service_type)
        result = {
            "rent_type": None,
            "container_feet": None,
            "min_commitment": None,
            "square_feet_size":None,
            "ton_size":None,            
            "sqft_value": None,            
            "add_on_type":None,
            "add_on_service":None,
            "rate": None
        }
        item_price = frappe.db.sql("""
                SELECT price_list_rate
                FROM `tabItem Price`
                WHERE item_code = %s AND selling = 1
                AND (%s BETWEEN IFNULL(valid_from, %s) AND IFNULL(valid_upto, %s))
                ORDER BY valid_from DESC
                LIMIT 1
            """, (service_type, nowdate(), nowdate(), nowdate()), as_dict=1)

        result["rate"] = item_price[0].price_list_rate if item_price else None

        if item.custom_rent_type == "Container Based":
            result["rent_type"] = "Container Based"
            if item.custom_container_feat_size == "20":
                result["container_feet"] = "20"
                result["min_commitment"] = item.custom_container_min_commitment
            elif item.custom_container_feat_size == "40":
                result["container_feet"] = "40"
                result["min_commitment"] = item.custom_container_min_commitment
        elif item.custom_rent_type == "Sqft Based":
            result["rent_type"] = "Sqft Based"
            if item.custom_square_feet_size == "1000":
                result["square_feet_size"] = "1000"
                result["min_commitment"] = item.custom_sqft_min_commitment
            elif item.custom_square_feet_size == "500":
                result["square_feet_size"] = "500"
                result["min_commitment"] = item.custom_sqft_min_commitment
            elif item.custom_square_feet_size == "TON":
                result["square_feet_size"] = "TON"
                result["min_commitment"] = item.custom_sqft_min_commitment
                result["ton_size"]= item.custom_ton_size
        elif item.custom_rent_type == "Add On":
            result["rent_type"] = "Add On"
            if item.custom_add_on_type == "Loading":
                result["add_on_type"] = "Loading"
                result["add_on_service"] = item.custom_add_on_service
            elif item.custom_add_on_type == "Unloading":
                result["add_on_type"] = "Unloading"
                result["add_on_service"] = item.custom_add_on_service
            elif item.custom_add_on_type == "Crossing":
                result["add_on_type"] = "Crossing"
                result["add_on_service"] = item.custom_add_on_service
            
        # elif item.custom_container_based_rent == 1:
        #     result["container_feet"] = item.custom_container_feat_size
        #     result["min_commitment"] = item.custom_container_min_commitment


        # elif item.custom_sqft_based_rent == 1:
        #     result["sqft_type"] = item.custom_sqft_type
            
        #     if item.custom_sqft_type == "Ton Based":
        #         if item.custom_80_ton == 1:
        #             result["sqft_value"] = "80 Ton"
        #             result["ton_sqft"] = item.custom_ton_based_sqft
        #             result["min_commitment"] = item.custom_sqft_min_commitment
        #         elif item.custom_40_ton == 1:
        #             result["sqft_value"] = "40 Ton"
        #             result["ton_sqft"] = item.custom_ton_based_sqft
        #             result["min_commitment"] = item.custom_sqft_min_commitment
                
        #     elif item.custom_sqft_type == "Container Based" :
        #         result["sqft_value"] = "Container"
        #         result["container_sqft"] = item.custom_container_based_sqft
        #         result["min_commitment"] = item.custom_sqft_min_commitment
                
        return result
        
    except Exception as e:
        frappe.log_error(f"Error fetching item data: {str(e)}")
        frappe.throw(f"Error fetching item data: {str(e)}")


# @frappe.whitelist()
# def get_valid_service_items(doctype, txt, searchfield, start, page_len, filters):

#     return frappe.db.sql("""
#         SELECT name, item_name
#         FROM `tabItem`
#         WHERE disabled = 0 AND (
#             custom_rent_type = "Container Based"
#             OR custom_rent_type = "Sqft Based"
#             OR custom_rent_type = "Add on"
#         ) AND ({0} LIKE %s OR item_name LIKE %s)
#         ORDER BY idx DESC
#         LIMIT %s OFFSET %s
#     """.format(searchfield), ('%%%s%%' % txt, '%%%s%%' % txt, page_len, start))


@frappe.whitelist()
def get_valid_service_items(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT name, item_name
        FROM `tabItem`
        WHERE disabled = 0 AND (
            custom_rent_type = "Container Based"
            OR custom_rent_type = "Sqft Based"
            OR custom_rent_type = "Add on"
        )
        ORDER BY idx DESC
    """, as_list=True)




import frappe
from frappe.utils import getdate, nowdate
from datetime import datetime, timedelta

def run_day_before_last_day():
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)
    return day_after_tomorrow.month != tomorrow.month

@frappe.whitelist(allow_guest=True)
def create_monthly_sales_invoice():
    frappe.log_error("Monthly Invoice")

    # Uncomment to run only day before last day
    # if not run_day_before_last_day():
    #     return

    today = getdate(nowdate())
    from_date = today.replace(day=1)
    to_date = (from_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    consignments = frappe.get_all("Inward Entry", filters={
        "docstatus": 1,
        "invoice_generated": 0
    }, fields=["name"])
    
    filtered_consignments = []
    for c in consignments:
        invoice_exists = frappe.db.exists("Sales Invoice", {
            "custom_reference_doctype": "Inward Entry",
            "custom_reference_docname": c.name,
            "custom_invoice_type": "Monthly Billing",
            "posting_date": ["between", [from_date, to_date]],
            "docstatus": ["<", 2]
        })
        if not invoice_exists:
            filtered_consignments.append(c)
    frappe.log_error("Filtered Consignments: ",filtered_consignments)

    for consignment in filtered_consignments:
        frappe.log_error("Consignment: ", consignment.name)
        try:
            generate_invoice_for_consignment(consignment.name, today)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Monthly Invoice Failed for {consignment.name}")



def generate_invoice_for_consignment(consignment_id, billing_date):
    frappe.log_error("consignment_id: ", consignment_id)
    from collections import defaultdict

    consignment = frappe.get_doc("Inward Entry", consignment_id)
    traffic_config = consignment.customer_tariff_config or []
    if not traffic_config and consignment.customer:
        customer = frappe.get_doc("Customer", consignment.customer)
        traffic_config = customer.customer_traffic_config
    if not traffic_config:
        return

    containers = frappe.get_all("Inward Entry Item", filters={"parent": consignment_id}, fields=["name", "container_arrival_date", "container_size"])

    item_map = {}
    sqft_by_date = defaultdict(list)

    for container in containers:
        # frappe.log_error("Container: ", container.name)

       
        total_inward = frappe.db.get_value("Inward Entry Item", container.name, "qty") or 0
        used_outward = frappe.db.sql("""
            SELECT SUM(oi.qty) FROM `tabOutward Entry Items` oi
            JOIN `tabOutward Entry` o ON o.name = oi.parent
            WHERE o.consignment = %s AND oi.container = %s
        """, (consignment_id, container.name))[0][0] or 0
        # frappe.log_error("used_outward: ", used_outward)

        outward_date = frappe.db.sql("""
            SELECT MAX(o.date) FROM `tabOutward Entry` o
            JOIN `tabOutward Entry Items` oi ON oi.parent = o.name
            WHERE o.consignment = %s AND oi.container = %s
        """, (consignment_id, container.name))[0][0]
        # frappe.log_error("outward_date: ", outward_date)

        if not outward_date:
            continue


        arrival_date = getdate(container.container_arrival_date)
        end_date = getdate(outward_date) if outward_date else billing_date
        days_stayed = (end_date - arrival_date).days or 1


        outward_dates = frappe.db.sql("""
                SELECT o.date, SUM(oi.qty) AS qty
                FROM `tabOutward Entry` o
                JOIN `tabOutward Entry Items` oi ON oi.parent = o.name
                WHERE o.consignment = %s AND oi.container = %s
                GROUP BY o.date
                ORDER BY o.date ASC
            """, (consignment_id, container.name), as_dict=True)
        # frappe.log_error("outward_dates: ", outward_dates)

        threshold_qty_75 = total_inward * 0.75
        threshold_qty_87_5 = total_inward * 0.875
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
                    key = f"{traffic.service_type}|{arrival_date}|{end_date}|container"
                    item_map[key] = {
                        "item_code": traffic.service_type,
                        "qty": 1,
                        "uom": "Day",
                        "rate": rate * duration,
                        "description": (
                            f"From {arrival_date.strftime('%d.%m.%y')} to {end_date.strftime('%d.%m.%y')}<br>"
                            f"{duration} Days * {rate} = {rate * duration}<br>"
                            f"(1*{container.container_size})"
                        )
                    }
            elif service_item.custom_rent_type == "Sqft Based":                
                sqft_by_date[end_date].append({
                    "sqft": raw_sqft,
                    "arrival_date": arrival_date,
                    "days_stayed": days_stayed,
                    "container_id": container.name
                })

    for end_date, containers in sqft_by_date.items():
        total_sqft = sum(c["sqft"] for c in containers)
        arrival_date = containers[0]["arrival_date"]
        min_days = min(c["days_stayed"] for c in containers)        

        sqft_configs = sorted(
            [tc for tc in traffic_config if frappe.get_value("Item", tc.service_type, "custom_rent_type") == "Sqft Based"],
            key=lambda x: int(x.square_feet_size or 0), reverse=True
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
            key = f"{config.service_type}|{arrival_date}|{end_date}|{block_size}"
            item_map[key] = {
                "item_code": config.service_type,
                "qty": block_count,
                "uom": "Day",
                "rate": rate * duration * block_count,
                "description": (
                    f"From {arrival_date.strftime('%d.%m.%y')} to {end_date.strftime('%d.%m.%y')}<br>"
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

    # frappe.log_error("Item Map: ", item_map)

    invoice_items = [i for i in item_map.values() if i["qty"] > 0]
    # frappe.log_error(f"Invoice Items: {invoice_items}")
    if not invoice_items:
        return  
    invoice = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": consignment.customer,
        "posting_date": getdate(nowdate()),
        "custom_reference_doctype": "Inward Entry",
        "custom_reference_docname": consignment.name,
        "custom_invoice_type": "Monthly Billing",
        "items": invoice_items
    })              
    invoice.insert()
    
    consignment.monthly_invoice_generated = 1
    # consignment.sales_invoice = invoice.name
    consignment.save()

   