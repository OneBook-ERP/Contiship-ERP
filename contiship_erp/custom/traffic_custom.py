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








from frappe.utils import getdate, nowdate, formatdate
import frappe
import calendar
from datetime import datetime, timedelta

@frappe.whitelist()
def generate_monthly_container_invoices(now=None):
    try:
        frappe.log_error("generate_monthly_container_invoices")
        today = getdate(nowdate())
        year = today.year
        month = today.month
        days_in_month = calendar.monthrange(year, month)[1]
        if today != getdate(f"{year}-{month:02d}-{days_in_month - 1}") and not now:
            return "Not scheduled date"
        first_day = datetime(today.year, today.month, 1).date()
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_of_month = datetime(today.year, today.month, last_day).date()

        inward_entries = frappe.get_all("Inward Entry", filters={
            "docstatus": 1,
            "invoice_generated": 0,        
        }, fields=["name", "monthly_invoice_date","arrival_date"])
        filtered_entries = [
            entry for entry in inward_entries
            if (
                not entry.monthly_invoice_date or
                getdate(entry.monthly_invoice_date).month != month or
                getdate(entry.monthly_invoice_date).year != year
            )
            and (
                getdate(entry.arrival_date).month == month and
                getdate(entry.arrival_date).year == year
            )
        ]

        for inward in filtered_entries:
            inward = frappe.get_doc("Inward Entry", inward.name)
            invoice_items = []
            all_dates = []
            default_company = frappe.defaults.get_user_default("Company")
            income_account = frappe.get_value("Company", default_company, "default_income_account")

            for item in inward.inward_entry_items:
                if item.crossing_item:
                    continue
                container = item.name
                container_size = item.container_size
                arrival_date = getdate(item.container_arrival_date)
                inward_qty = item.qty

                tariffs = inward.customer_tariff_config or frappe.get_doc("Customer", inward.customer).custom_customer_traffic_config
                tariff = next((
                    t for t in tariffs 
                    if (
                        (t.rent_type == "Container Based" and str(t.container_feet) == str(container_size)) or
                        (t.rent_type == "LCL" and str(t.lcl_type) == str(container_size))
                    )
                ), None)

                if not tariff:
                    continue

                items = frappe.get_all("Outward Entry Items", filters={"container": container, "parenttype": "Outward Entry", "crossing_item": 0},fields=["qty", "parent"])
                outward_items = []

                for item in items:
                    billed = frappe.db.get_value("Outward Entry", item["parent"], "billed")
                    if not billed:
                        item["date"] = frappe.db.get_value("Outward Entry", item["parent"], "date")
                        outward_items.append(item)
                # for item in outward_items:
                #     item["date"] = frappe.db.get_value("Outward Entry", item["parent"], "date")
                frappe.log_error("Outward Items: ", outward_items)

                if not outward_items:
                    # No outward case
                    start_date = max(arrival_date, first_day)
                    end_date = end_of_month
                    duration = (end_date - start_date).days + 1
                    if duration < tariff.minimum_commitmentnoofdays:
                        effective_days = tariff.minimum_commitmentnoofdays
                        end_date = start_date + timedelta(days=effective_days - 1)
                    else:
                        effective_days = duration               

                    rate = tariff.rate         

                    item_name = frappe.get_value("Item", tariff.service_type, "item_name")
                    invoice_items.append({
                        "item_code": tariff.service_type,
                        "item_name": item_name,
                        "qty": effective_days,
                        "rate": rate,
                        "uom": tariff.uom or "Day",
                        "description": f"From {formatdate(start_date)} to {formatdate(end_date)}",
                        "income_account": income_account,
                        "custom_bill_from_date":start_date,
                        "custom_bill_to_date": end_date,
                        "custom_container": container,
                        "custom_container_status": "Pending",
                        "custom_invoice_type": "Monthly Billing"                    
                    })
                    all_dates.extend([start_date, end_date])
                else:
                    dispatched_total = 0
                    prev_end = None
                    if tariff.enable_875_rule or tariff.enable_75_rule:                                
                        outward_items = sorted(outward_items, key=lambda x: getdate(x["date"]))                      
                        
                        current_start_date = max(arrival_date if not prev_end else prev_end + timedelta(days=1), first_day)
                        slabs = []

                        final_outward_date = max(getdate(r["date"]) for r in outward_items)                                                       
                        final_invoice_date = min(
                            max(final_outward_date, arrival_date + timedelta(days=tariff.minimum_commitmentnoofdays - 1)),
                            end_of_month
                        )
                        duration_days = (final_invoice_date - arrival_date).days + 1
                        effective_days = max(duration_days, tariff.minimum_commitmentnoofdays)

                        for idx, row in enumerate(outward_items):
                            current_date = getdate(row["date"])
                        
                            dispatched_before_current = dispatched_total   
                            dispatched_total += row["qty"]
                            dispatched_percent = (dispatched_before_current / inward_qty) * 100 if inward_qty else 0

                            
                            if tariff.enable_875_rule and dispatched_percent >= 87.5:
                                rate = tariff.after_875discounted_rate
                                slab_type = "87.5"
                            elif tariff.enable_75_rule and dispatched_percent >= 75:
                                rate = tariff.after_75_discounted_rate
                                slab_type = "75"
                            else:
                                rate = tariff.rate
                                slab_type = "normal"
                            
                            if idx + 1 < len(outward_items):
                                next_date = getdate(outward_items[idx + 1]["date"]) - timedelta(days=1)
                            else:
                                next_date = final_invoice_date
                            
                            if next_date < current_start_date:
                                continue

                            slabs.append({
                                "from_date": current_start_date,
                                "to_date": next_date,
                                "rate": rate,
                                "slab_type": slab_type
                            })

                            current_start_date = next_date + timedelta(days=1)
                            outward = frappe.get_doc("Outward Entry", row["parent"])
                            outward.billed = 1
                            outward.save()
                    
                        item_name = frappe.get_value("Item", tariff.service_type, "item_name")

                        merged_slabs = []
                        for slab in slabs:
                            if not merged_slabs:
                                merged_slabs.append(slab)
                            else:
                                last = merged_slabs[-1]
                                # Merge if rate and slab_type match and dates are contiguous
                                if slab["rate"] == last["rate"] and slab["slab_type"] == last["slab_type"] and slab["from_date"] == last["to_date"] + timedelta(days=1):
                                    # Extend last slab's to_date
                                    last["to_date"] = slab["to_date"]
                                else:
                                    merged_slabs.append(slab)

                        for slab in merged_slabs:
                            slab_days = (slab["to_date"] - slab["from_date"]).days + 1
                            invoice_items.append({
                                "item_code": tariff.service_type,
                                "item_name": item_name,
                                "rate": slab["rate"],
                                "qty": slab_days,
                                "uom": tariff.uom or "Day",
                                "description": f"From {slab['from_date'].strftime('%d-%m-%Y')} to {slab['to_date'].strftime('%d-%m-%Y')}",
                                "income_account": income_account,
                                "custom_bill_from_date": slab["from_date"],
                                "custom_bill_to_date": slab["to_date"],
                                "custom_container": container,
                                "custom_container_status": "Completed" if dispatched_total >= inward_qty else "Partial",
                                "custom_invoice_type": "Monthly Billing",
                                "custom_outward_qty": dispatched_total
                            })
                            all_dates.extend([slab['from_date'], slab['to_date']])
                            prev_end = slab['to_date']
                    
                    # dispatched_total = 0
                    # prev_end = None

                    # for row in sorted(outward_items, key=lambda x: getdate(x["date"])):
                    #     if not tariff.enable_875_rule and not tariff.enable_75_rule:                    
                    #         continue
                    #     current_date = getdate(row["date"])
                    #     qty_out = row["qty"]
                    #     dispatched_before_current = dispatched_total                    
                    #     dispatched_total += qty_out
                    #     frappe.log_error("dispatched_total", dispatched_total)
                    #     dispatched_percent = (dispatched_before_current / inward_qty) * 100 if inward_qty else 0
                    #     frappe.log_error("dispatched_percent", dispatched_percent)
                        
                    #     if tariff.enable_875_rule and dispatched_percent >= 87.5:
                    #         rate = tariff.after_875discounted_rate
                    #     elif tariff.enable_75_rule and dispatched_percent >= 75:
                    #         rate = tariff.after_75_discounted_rate
                    #     else:
                    #         rate = tariff.rate

                    #     # Calculate billing period
                    #     start_date = max(arrival_date if not prev_end else prev_end + timedelta(days=1), first_day)
                    #     if (current_date - arrival_date).days < tariff.minimum_commitmentnoofdays:
                    #         display_last_outward_date = arrival_date + timedelta(days=tariff.minimum_commitmentnoofdays - 1)
                    #     else:
                    #         display_last_outward_date = current_date
                    #     end_date = min(display_last_outward_date, end_of_month)

                    #     duration_days = (end_date - start_date).days + 1
                    #     if duration_days <= 0:
                    #         continue

                    #     item_name = frappe.get_value("Item", tariff.service_type, "item_name")
                    #     invoice_items.append({
                    #         "item_code": tariff.service_type,
                    #         "item_name": item_name,
                    #         "rate": rate,
                    #         "qty": duration_days,
                    #         "uom": tariff.uom or "Day",
                    #         "description": f"From {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}",
                    #         "income_account": income_account,
                    #         "custom_bill_from_date": start_date,
                    #         "custom_bill_to_date": end_date,
                    #         "custom_container": container,
                    #         "custom_container_status": "Completed" if dispatched_total >= inward_qty else "Partial",
                    #         "custom_invoice_type": "Monthly Billing",
                    #         "custom_outward_qty": qty_out
                    #     })

                    #     all_dates.extend([start_date, end_date])
                    #     prev_end = end_date

                    if not tariff.enable_875_rule and not tariff.enable_75_rule:
                        final_outward_date = max(getdate(r["date"]) for r in outward_items)
                        dispatched_total = sum(r["qty"] for r in outward_items if r.get("qty"))
                        actual_last_outward_date = final_outward_date
                    
                        if (final_outward_date - arrival_date).days < tariff.minimum_commitmentnoofdays:
                            display_last_outward_date = arrival_date + timedelta(days=tariff.minimum_commitmentnoofdays - 1)
                        else:
                            display_last_outward_date = final_outward_date

                        duration_days = (actual_last_outward_date - arrival_date).days + 1
                        effective_days = max(duration_days, tariff.minimum_commitmentnoofdays)

                        description = f"From {arrival_date.strftime('%d-%m-%Y')} to {display_last_outward_date.strftime('%d-%m-%Y')}"
                        item_name = frappe.get_value("Item", tariff.service_type, "item_name")

                        invoice_items.append({
                            "item_code": tariff.service_type,
                            "item_name": item_name,
                            "rate": tariff.rate,
                            "qty": effective_days,
                            "uom": tariff.uom or "Day",
                            "description": description,
                            "income_account": income_account,
                            "custom_bill_from_date": arrival_date,
                            "custom_bill_to_date": display_last_outward_date,
                            "custom_container": container,
                            "custom_container_status": "Completed" if dispatched_total >= inward_qty else "Partial",
                            "custom_invoice_type": "Monthly Billing",
                            "custom_outward_qty": dispatched_total
                        })
                        all_dates.extend([arrival_date, display_last_outward_date])
                        for item in outward_items:
                            outward = frappe.get_doc("Outward Entry", item["parent"])
                            outward.billed = 1
                            outward.save()
                
                    if dispatched_total < inward_qty and prev_end and prev_end < end_of_month:                
                        start_date = prev_end + timedelta(days=1)
                        end_date = end_of_month
                        duration = (end_date - start_date).days + 1

                        if duration > 0:
                            rate = tariff.rate
                            item_name = frappe.get_value("Item", tariff.service_type, "item_name")
                            invoice_items.append({
                                "item_code": tariff.service_type,
                                "item_name": item_name,
                                "qty": duration,
                                "rate": rate,
                                "uom": tariff.uom or "Day",
                                "description": f"From {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')} (Post last outward)",
                                "income_account": income_account,
                                "custom_bill_from_date": start_date,
                                "custom_bill_to_date": end_date,
                                "custom_container": container,
                                "custom_container_status": "Partial",
                                "custom_invoice_type": "Monthly Billing"
                            })
                            all_dates.extend([start_date, end_date])


            if invoice_items:
                si = frappe.new_doc("Sales Invoice")
                si.customer = inward.customer
                si.posting_date = nowdate()
                si.custom_reference_doctype = "Inward Entry"
                si.custom_reference_docname = inward.name
                si.custom_invoice_type = "Monthly Billing"
                si.custom_consignment = inward.boeinvoice_no
                si.set("items", invoice_items)
                si.custom_bill_from_date = min(all_dates) if all_dates else first_day
                si.custom_bill_to_date = max(all_dates) if all_dates else end_of_month
                si.insert()
                frappe.db.commit()

                inward.monthly_invoice_date = nowdate()
                inward.save()
        
        return "Invoice Created"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Container Invoice Monthly Generation Failed")
        frappe.throw("An error occurred while generating the container monthly invoice.")