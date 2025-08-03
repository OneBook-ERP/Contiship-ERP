import frappe
import calendar
from datetime import datetime
from frappe.utils import nowdate, getdate
from collections import defaultdict

@frappe.whitelist()
def fetch_item_data(service_type):
    try:
        item = frappe.get_doc("Item", service_type)
        result = {
            "rent_type": None,
            "container_feet": None,
            "min_commitment": None,
            "square_feet_size":None,
            "additional_sqft_size":None,            
            "sqft_value": None,            
            "add_on_type":None,
            "add_on_service":None,
            "rate": None,
            "uom": None
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
        elif item.custom_rent_type == "LCL":
            result["rent_type"] = "LCL"
            if item.custom_lcl_type == "Tata Ac":
                result["container_feet"] = "Tata Ac"                
            elif item.custom_lcl_type == "Eicher":
                result["container_feet"] = "Eicher"
            elif item.custom_lcl_type == "Lorry":
                result["container_feet"] = "Lorry"
            elif item.custom_lcl_type == "Trurus1":
                result["container_feet"] = "Trurus1"
            elif item.custom_lcl_type == "Trurus2":
                result["container_feet"] = "Trurus2"
                
        elif item.custom_rent_type == "Sqft Based":
            result["rent_type"] = "Sqft Based"
            if item.custom_square_feet_size == "1000":
                result["square_feet_size"] = "1000"
                result["min_commitment"] = item.custom_sqft_min_commitment
            elif item.custom_square_feet_size == "500":
                result["square_feet_size"] = "500"
                result["min_commitment"] = item.custom_sqft_min_commitment
            elif item.custom_square_feet_size == "Additional":
                result["square_feet_size"] = "Additional"
                result["min_commitment"] = item.custom_sqft_min_commitment
                result["additional_sqft_size"]= item.custom_additional_sqft_size
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
                            
        return result
        
    except Exception as e:
        frappe.log_error(f"Error fetching item data: {str(e)}")
        frappe.throw(f"Error fetching item data: {str(e)}")

@frappe.whitelist()
def get_valid_service_items(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT name, item_name
        FROM `tabItem`
        WHERE disabled = 0 AND (
            custom_rent_type = "Container Based"
            OR custom_rent_type = "Sqft Based"
            OR custom_rent_type = "Add on"
            OR custom_rent_type = "LCL"
        )
        ORDER BY idx DESC
    """, as_list=True)

def sales_invoice_on_submit(doc, method):
    from frappe.model.rename_doc import rename_doc
    from frappe.model.naming import make_autoname
    import datetime

    year = datetime.datetime.now().strftime("%Y")
    new_name = make_autoname(f"ACC-SINV-{year}-.#####")

    if doc.name != new_name:
        rename_doc("Sales Invoice", doc.name, new_name, force=True)
        frappe.db.set_value("Sales Invoice", new_name, "name", new_name)
        frappe.db.commit()
        frappe.log_error("Renamed Invoice", f"{doc.name} ➜ {new_name}")



# ----------------------------INVOICE CREATION----------------------------

@frappe.whitelist()
def create_monthly_standard_sqft_invoice(start=None):
    if start == 1:
        today_obj = getdate(nowdate())
        year = today_obj.year
        month = today_obj.month
        today = datetime(year, month, 1).date()
    else:
        today = getdate(nowdate())
    year = today.year
    month = today.month
    days_in_month = calendar.monthrange(year, month)[1]

    start_date = getdate(f"{year}-{month:02d}-01")
    end_date = getdate(f"{year}-{month:02d}-{days_in_month}")

    sqft_traffic = frappe.db.get_all(
        "Customer Traffic Config",
        filters={
            "rent_type": "Sqft Based",
            "square_feet_size": ("!=", "Additional")
        },
        fields=["parent as customer", "service_type", "square_feet_size", "minimum_commitmentnoofdays", "rate", "uom"]
    )

    if not sqft_traffic:
        frappe.log_error("No Sqft Based traffic records found.", "Monthly Invoice")
        return

    customer_services = defaultdict(list)
    for row in sqft_traffic:
        customer_services[row.customer].append(row)

    for customer, services in customer_services.items():       
        invoice_date = frappe.db.get_value("Customer", customer, "custom_standard_sqft_invoice_date")
        if invoice_date:
            invoice_date = getdate(invoice_date)
            if invoice_date.year == year and invoice_date.month == month:
                continue

        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = customer
        invoice.posting_date = today
        invoice.due_date = today

        for service in services:
            uom = service.uom or "Sqf"
            invoice.append("items", {
                "item_code": service.service_type,
                "item_name": service.service_type,
                "description": f"{start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}",
                "qty": service.square_feet_size,
                "rate": service.rate,
                "uom": uom
            })

        try:
            invoice.insert(ignore_permissions=True)         
            frappe.db.set_value("Customer", customer, "custom_standard_sqft_invoice_date", today)           

        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to create invoice for {customer}")
    return "Invoice Created"


@frappe.whitelist()
def create_monthly_additional_sqft_invoice(end=None):
    today = getdate(nowdate())
    year = today.year
    month = today.month
    days_in_month = calendar.monthrange(year, month)[1]
    
    if today != getdate(f"{year}-{month:02d}-{days_in_month - 1}") and not end:
        return "Not scheduled date"

    start_date = getdate(f"{year}-{month:02d}-01")
    end_date = getdate(f"{year}-{month:02d}-{days_in_month}")

    sqft_traffic = frappe.db.get_all(
        "Customer Traffic Config",
        filters={
            "rent_type": "Sqft Based",
            "square_feet_size": "Additional"
        },
        fields=["parent as customer", "service_type", "square_feet_size","additional_sqft_size", "minimum_commitmentnoofdays", "rate", "uom"]
    )

    if not sqft_traffic:
        frappe.log_error("No Additional Sqft Based traffic found", "Additional Invoice")
        return

    customer_services = defaultdict(list)
    for row in sqft_traffic:
        customer_services[row.customer].append(row)

    for customer, services in customer_services.items():
        invoice_date = frappe.db.get_value("Customer", customer, "custom_additional_sqft_invoice_date")
        if invoice_date:
            invoice_date = getdate(invoice_date)
            if invoice_date.year == year and invoice_date.month == month:
                continue

        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = customer
        invoice.posting_date = today
        invoice.due_date = today

        for service in services:
            uom = service.uom or "Sqf"
            invoice.append("items", {
                "item_code": service.service_type,
                "item_name": service.service_type,
                "description": f"{start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}",
                "qty": service.additional_sqft_size or "500",
                "rate": service.rate,
                "uom": uom
            })

        try:
            invoice.insert(ignore_permissions=True)
            frappe.db.set_value("Customer", customer, "custom_additional_sqft_invoice_date", today)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to create additional sqft invoice for {customer}")

    return "Additional Sqft Invoices Created"




import frappe
from frappe.utils import getdate, nowdate
from datetime import datetime, timedelta


def run_day_before_last_day():
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)
    return day_after_tomorrow.month != tomorrow.month

@frappe.whitelist(allow_guest=True)
def create_monthly_sales_invoice(monthly_invoice_generated=None):
    frappe.log_error("Monthly Invoice")

    
    if not run_day_before_last_day() and not monthly_invoice_generated:
        return

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
    return "Monthly Invoice Created"
    


def generate_invoice_for_consignment(consignment_id, billing_date):
    frappe.log_error("consignment_id: ", consignment_id)
    today = getdate()
    from collections import defaultdict

    consignment = frappe.get_doc("Inward Entry", consignment_id)
    traffic_config = consignment.customer_tariff_config or []
    if not traffic_config and consignment.customer:
        customer = frappe.get_doc("Customer", consignment.customer)
        traffic_config = customer.customer_traffic_config
    if not traffic_config:
        return

    containers = frappe.get_all(
        "Inward Entry Item",
        filters={"parent": consignment_id},
        fields=["name", "container_arrival_date", "container_size"]
    )

    item_map = {}
    sqft_by_date = defaultdict(list)

    for container in containers:
        total_inward = frappe.db.get_value("Inward Entry Item", container.name, "qty") or 0

        outward_date = frappe.db.sql("""
            SELECT MAX(o.date) FROM `tabOutward Entry` o
            JOIN `tabOutward Entry Items` oi ON oi.parent = o.name
            WHERE o.consignment = %s AND oi.container = %s
        """, (consignment_id, container.name))[0][0]

        if not outward_date:
            outward_date = billing_date


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

        end_date = getdate(outward_date) if outward_date else billing_date
        days_stayed = (end_date - arrival_date).days + 1

        outward_dates = frappe.db.sql("""
            SELECT o.date, SUM(oi.qty) AS qty
            FROM `tabOutward Entry` o
            JOIN `tabOutward Entry Items` oi ON oi.parent = o.name
            WHERE o.consignment = %s AND oi.container = %s
            GROUP BY o.date
            ORDER BY o.date ASC
        """, (consignment_id, container.name), as_dict=True)

        # Correct 75% / 87.5% rule
        apply_75_discount = False
        apply_87_5_discount = False
        dispatched_qty = 0
        if not outward_dates:
            for traffic in traffic_config:
                if traffic.rent_type == "Add On":
                        continue
                # No outward entries — treat as fully in storage
                outward_date = billing_date
                arrival_date = container.container_arrival_date
                days_stayed = (outward_date - arrival_date).days + 1
                if days_stayed < 0:
                    days_stayed = 0

                # Use item_map to accumulate
                key = traffic.service_type
                item_map.setdefault(key, {
                    "item_code": traffic.service_type,
                    "uom": "Day",
                    "qty": 0,
                    "rate": traffic.rate,
                    "description": f"{container.name} - {days_stayed} days (no outward)"
                })
                item_map[key]["qty"] += days_stayed

        else:

            for row in outward_dates:
                dispatched_qty += row.qty or 0
                dispatched_percent = (dispatched_qty / total_inward) * 100 if total_inward else 0
                if dispatched_percent >= 87.5:
                    apply_87_5_discount = True
                    break
                elif dispatched_percent >= 75:
                    apply_75_discount = True

                raw_sqft = int(container.container_size or 0) * 10 if container.container_size in ["20", "40"] else 0

                for traffic in traffic_config:
                    if traffic.rent_type == "Add On":
                        continue
                    service_item = frappe.get_doc("Item", traffic.service_type)

                    if not hasattr(service_item, 'custom_rent_type'):
                        continue

                    duration = max(days_stayed, traffic.minimum_commitmentnoofdays or 1)

                    if traffic.enable_875_rule and apply_87_5_discount:
                        rate = traffic.after_875discounted_rate
                    elif traffic.enable_75_rule and apply_75_discount:
                        rate = traffic.after_75_discounted_rate
                    else:
                        rate = traffic.rate

                    if container.container_size not in ["20", "40"]:
                        if str(container.container_size) == str(service_item.custom_lcl_type):
                            key = f"{traffic.service_type}|{arrival_date}|{end_date}|LCL"
                            item_map[key] = {
                                "item_code": traffic.service_type,
                                "qty": duration,
                                "uom": "Day",
                                "rate": rate,
                                "description": f"From {arrival_date.strftime('%d.%m.%y')} to {end_date.strftime('%d.%m.%y')}"
                            }

                    if service_item.custom_rent_type == "Container Based":
                        if str(container.container_size) == str(service_item.custom_container_feat_size):
                            key = f"{traffic.service_type}|{arrival_date}|{end_date}|container"
                            item_map[key] = {
                                "item_code": traffic.service_type,
                                "qty": duration,
                                "uom": "Day",
                                "rate": rate,
                                "description": f"From {arrival_date.strftime('%d.%m.%y')} to {end_date.strftime('%d.%m.%y')}"
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
            key=lambda x: int(x.square_feet_size or 0),
            reverse=True
        )

        remaining_sqft = total_sqft

        for config in sqft_configs:
            if config.rent_type == "Add On":
                continue
            block_size = int(config.square_feet_size or 0)
            if block_size <= 0:
                continue

            while remaining_sqft >= block_size:
                remaining_sqft -= block_size
                duration = max(min_days, config.minimum_commitmentnoofdays or 1)

                if config.enable_875_rule and apply_87_5_discount:
                    rate = config.after_875discounted_rate
                elif config.enable_75_rule and apply_75_discount:
                    rate = config.after_75_discounted_rate
                else:
                    rate = config.rate

                key = f"{config.service_type}|{arrival_date}|{end_date}|{block_size}"
                item_map[key] = {
                    "item_code": config.service_type,
                    "qty": duration,
                    "uom": "Day",
                    "rate": rate,
                    "description": f"From {arrival_date.strftime('%d.%m.%y')} to {end_date.strftime('%d.%m.%y')}"
                }

        if remaining_sqft > 0:
            fallback = next((t for t in traffic_config if t.square_feet_size == "500"), None)
            if fallback:
                duration = max(min_days, fallback.minimum_commitmentnoofdays or 1)

                if fallback.enable_875_rule and apply_87_5_discount:
                    rate = fallback.after_875discounted_rate
                elif fallback.enable_75_rule and apply_75_discount:
                    rate = fallback.after_75_discounted_rate
                else:
                    rate = fallback.rate

                key = f"{fallback.service_type}|{arrival_date}|{end_date}|500|Add On Service"
                item_map[key] = {
                    "item_code": fallback.service_type,
                    "qty": duration,
                    "uom": "Day",
                    "rate": rate,
                    "description": f"From {arrival_date.strftime('%d.%m.%y')} to {end_date.strftime('%d.%m.%y')}"
                }

    invoice_items = [i for i in item_map.values() if i["qty"] > 0]

    for item in invoice_items:
        # Add missing item_name
        if not item.get("item_name"):
            item["item_name"] = frappe.get_value("Item", item["item_code"], "item_name")

        # Add missing income_account
        if not item.get("income_account"):
            default_company = frappe.defaults.get_user_default("Company")
            income_account = frappe.get_value("Company", default_company, "default_income_account")
            item["income_account"] = income_account


    if not invoice_items:
        return

    invoice = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": consignment.customer,
        "posting_date": billing_date,
        "custom_reference_doctype": "Inward Entry",
        "custom_reference_docname": consignment.name,
        "custom_invoice_type": "Monthly Billing",
        "items": invoice_items
    })
    invoice.insert()

    consignment.monthly_invoice_generated = 1
    consignment.save()

