import frappe
import calendar
from datetime import datetime, timedelta
from frappe.utils import nowdate, getdate, formatdate
from collections import defaultdict
from frappe.model.rename_doc import rename_doc
from frappe.model.naming import make_autoname

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
            "uom": None,
            "lcl_type": None
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
            result["lcl_type"] = "LCL"           
                
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


def sales_invoice_before_submit(doc, method):
    import datetime
    from frappe.utils import getdate
    doc.due_date = getdate(doc.posting_date) + datetime.timedelta(days=7)


def sales_invoice_on_submit(doc, method):
    import datetime    
    from frappe.model.rename_doc import rename_doc
    from frappe.model.naming import make_autoname

    year = datetime.datetime.now().year
    current = str(year)[-2:]
    next_year = str(year + 1)[-2:]

    new_name = make_autoname(f"GWH/{current}-{next_year}/.###")
    if doc.is_return:
        new_name = make_autoname(f"CH/{current}-{next_year}/.###")

    if doc.name != new_name:
        rename_doc("Sales Invoice", doc.name, new_name, force=True)
        frappe.db.set_value("Sales Invoice", new_name, "name", new_name)
        frappe.db.commit()


def sales_invoice_after_insert(doc, method):    
    if doc.taxes_and_charges:
        taxes_template = frappe.get_doc("Sales Taxes and Charges Template", doc.taxes_and_charges)

        if taxes_template.taxes:
            doc.set("taxes", [t.as_dict() for t in taxes_template.taxes])
            doc.save(ignore_permissions=True)
            frappe.db.commit()
        else:
            if frappe.db.exists("GST Settings"):
                gst_settings = frappe.get_doc("GST Settings")
                output_accounts = None
                for acc in gst_settings.gst_accounts:                    
                    if acc.account_type == "Output":
                        output_accounts = acc
                        break
            if not output_accounts:
                frappe.log_error("No GST Output Accounts found in GST Settings for this company")

            if "In-state" in doc.taxes_and_charges:
                doc.append("taxes", {
                    "charge_type": "On Net Total",
                    "account_head": output_accounts.cgst_account,
                    "rate": 9.0,
                    "description": "CGST @ 9%"
                })               
                doc.append("taxes", {
                    "charge_type": "On Net Total",
                    "account_head": output_accounts.sgst_account,
                    "rate": 9.0,
                    "description": "SGST @ 9%"
                })
                doc.save(ignore_permissions=True)
                frappe.db.commit()

            elif "Out-state" in doc.taxes_and_charges:                
                doc.append("taxes", {
                    "charge_type": "On Net Total",
                    "account_head": output_accounts.igst_account,
                    "rate": 18.0,
                    "description": "IGST @ 18%"
                })
                doc.save(ignore_permissions=True)
                frappe.db.commit()



@frappe.whitelist()
def get_sidebar_items():
    doc = frappe.get_doc("Contiship Settings", "Contiship Settings")
    items = doc.items
    allowed_items = []
    user = frappe.session.user
    for item in items:
        allowed = True
        if item.reference_type and item.reference_to:

            if item.reference_type == "DocType":
                if not frappe.has_permission(item.reference_to, "read", user=user):
                    allowed = False
            elif item.reference_type == "Page":
                if not frappe.has_permission("Page", "read", doc=item.reference_to, user=user):
                    allowed = False              
            elif item.reference_type == "Report":               
                if not frappe.has_permission("Report", "read", doc=item.reference_to, user=user):
                    allowed = False
        if allowed:
            allowed_items.append({
                "icon": item.icon,
                "label": item.label,
                "redirect_url": item.redirect_url,
                "parent_item": item.parent_item,
                "reference_type": item.reference_type,
                "reference_to": item.reference_to,
            })
    return {
        "items": allowed_items,
        "enabled": doc.enable_sidebar,
        "toggle_default_sidebar": doc.toggle_default_sidebar,
        "home_page": doc.home_page
    }




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
        invoice.custom_invoice_type = "Storage"

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
    
    if today != getdate(f"{year}-{month:02d}-{days_in_month - 2}") and not end:
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
        invoice.custom_invoice_type = "Storage"

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



@frappe.whitelist()
def generate_monthly_container_invoices(now=None):
    try:
        if not frappe.db.exists("UOM", {"name": "Day"}):
            frappe.get_doc({
                "doctype": "UOM",               
                "uom_name": "Day",                
            }).insert(ignore_permissions=True)
        today = getdate(nowdate())
        year = today.year
        month = today.month
        days_in_month = calendar.monthrange(year, month)[1]
        if today != getdate(f"{year}-{month:02d}-{days_in_month - 2}") and not now:
            return "Not scheduled date"
        first_day = datetime(today.year, today.month, 1).date()
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_of_month = datetime(today.year, today.month, last_day).date()

        inward_entries = frappe.get_all("Inward Entry", filters={
            "docstatus": 1,
            "invoice_generated": 0,
            "storage_bill": 1,
            "service_type": "Others"

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
            container_map = {}
            default_company = frappe.defaults.get_user_default("Company")
            income_account = frappe.get_value("Company", default_company, "default_income_account")

            for item in inward.inward_entry_items:
                container_name = item.container
                if not container_name:
                    continue
                if item.crossing_item:
                    continue                
                if container_name not in container_map:
                    container_map[container_name] = {
                        "items": [item],
                        "total_qty": item.qty,
                        "container_size": item.container_size,
                        "arrival_date": getdate(item.container_arrival_date),
                        "container_name": item.container,
                        "name": item.name
                    }
                else:
                    container_map[container_name]["items"].append(item)
                    container_map[container_name]["total_qty"] += item.qty

            for container_name, data in container_map.items():
                items_list = data["items"]
                item = items_list[0]                             
                inward_qty = data["total_qty"]
                container_name = data["container_name"]
                container_size = data["container_size"]
                arrival_date = data["arrival_date"]
                container = data["name"]
                frappe.log_error(f"inward_qty: {inward_qty}")

            # for item in inward.inward_entry_items:
               
               
            #     container = item.name
            #     container_name = item.container
            #     container_size = item.container_size
            #     arrival_date = getdate(item.container_arrival_date)
            #     inward_qty = item.qty

                # tariffs = inward.customer_tariff_config or frappe.get_doc("Customer", inward.customer).custom_customer_traffic_config
                # tariff = next((
                #     t for t in tariffs 
                #     if (
                #         (t.rent_type == "Container Based" and str(t.container_feet) == str(container_size)) or
                #         (t.rent_type == "LCL" and str(t.lcl_type) == str(container_size))
                #     )
                # ), None)

                # if not tariff:
                #     continue

                # items = frappe.get_all("Outward Entry Items", filters={"container": container, "parenttype": "Outward Entry", "crossing_item": 0},fields=["qty", "parent"])

                parents = frappe.get_all("Outward Entry",
                    filters={
                        "consignment": inward.name,                                                     
                    },
                    pluck="name"
                )
                items = frappe.get_all("Outward Entry Items", filters={"container_name": container_name, "parent": ["in", parents], "parenttype": "Outward Entry", "crossing_item": 0},fields=["qty", "parent"], order_by="creation ASC")
                outward_items = []

                for oitem in items:
                    billed = frappe.db.get_value("Outward Entry", oitem["parent"], "billed")
                    if not billed:
                        oitem["date"] = frappe.db.get_value("Outward Entry", oitem["parent"], "date")
                        outward_items.append(oitem)              
                
                if not outward_items:
                    # No outward case
                    start_date = max(arrival_date, first_day)
                    end_date = end_of_month
                    duration = (end_date - start_date).days + 1
                    if duration < (item.minimum_commitmentnoofdays or 0):
                        effective_days = item.minimum_commitmentnoofdays or 0
                        end_date = start_date + timedelta(days=effective_days - 1)
                    else:
                        effective_days = duration               

                    rate = item.rate         

                    item_name = frappe.get_value("Item", item.service_type, "item_name")                   
                    invoice_items.append({
                        "item_code": item.service_type,
                        "item_name": item_name,
                        "qty": effective_days,
                        "rate": rate,
                        "uom": "Day",
                        "description": f"From {formatdate(start_date)} to {formatdate(end_date)}",
                        "income_account": income_account,
                        "custom_bill_from_date":start_date,
                        "custom_bill_to_date": end_date,
                        "custom_container": container,
                        "custom_container_name": container_name,
                        "custom_container_status": "Pending",
                        "custom_invoice_type": "Monthly Billing"                    
                    })
                    all_dates.extend([start_date, end_date])
                else:

                    dispatched_total = 0
                    prev_end = None

                    if item.enable_875_rule or item.enable_75_rule:
                        current_start_date = arrival_date
                        if month_invoice_details:
                            dispatched_total = get_billed_qty(container)
                        slabs = []
                
                        final_outward_date = max(getdate(r["date"]) for r in outward_items)
                        final_duration_days = (final_outward_date - arrival_date).days + 1
                        commitment_days = item.minimum_commitmentnoofdays if not month_invoice_details else 0
                        for idx, row in enumerate(outward_items):
                            outward_date = getdate(row["date"])
                            duration_days = (outward_date - current_start_date).days + 1
                            dispatched_before_current = dispatched_total   
                            dispatched_total += row["qty"]
                            dispatched_percent = (dispatched_before_current / inward_qty) * 100 if inward_qty else 0

                            if not final_duration_days<commitment_days and duration_days<commitment_days and idx==0 :
                                frappe.log_error("commitment_days", commitment_days)                       
                                outward_date = arrival_date + timedelta(days=commitment_days-1)
                                frappe.log_error("outward_date", outward_date)
                                

                            if item.enable_75_rule and dispatched_percent >= 75 and (final_duration_days>commitment_days):
                                rate = item.after_75_discounted_rate
                                slab_type = "75"
                            elif item.enable_875_rule and dispatched_percent >= 87.5 and (final_duration_days>commitment_days):
                                rate = item.after_875discounted_rate
                                slab_type = "87.5"                    
                            else:
                                rate = item.rate
                                slab_type = "0"

                            # if idx + 1 < len(outward_items):
                            #     next_date = getdate(outward_items[idx]["date"])
                            #     frappe.log_error("next_date1", next_date)
                            # else:
                            next_date = outward_date
                            frappe.log_error("next_date2", next_date)

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

                        item_name = frappe.get_value("Item", item.service_type, "item_name")                
                        merged_slabs = []
                        frappe.log_error("slabs", slabs)
                        for slab in slabs:
                            if not merged_slabs:
                                merged_slabs.append(slab)
                            else:
                                last = merged_slabs[-1]                        
                                if slab["rate"] == last["rate"] and slab["slab_type"] == last["slab_type"] and slab["from_date"] == last["to_date"] + timedelta(days=1):                            
                                    last["to_date"] = slab["to_date"]
                                else:
                                    merged_slabs.append(slab)            

                        for slab in merged_slabs:
                            slab_days = (slab["to_date"] - slab["from_date"]).days + 1
                            invoice_items.append({
                                "item_code": item.service_type,
                                "item_name": item_name,
                                "rate": slab["rate"],
                                "qty": slab_days,
                                "uom": "Day",
                                "description": f"From {slab['from_date'].strftime('%d-%m-%Y')} to {slab['to_date'].strftime('%d-%m-%Y')}",
                                "income_account": income_account,
                                "custom_bill_from_date": slab["from_date"],
                                "custom_bill_to_date": slab["to_date"],
                                "custom_container": container,
                                "custom_container_name": container_name,                      
                                "custom_container_status": "Completed",
                                "custom_invoice_type": "Immediate Billing",                        
                            })
                            all_dates.extend([slab['from_date'], slab['to_date']])
                            prev_end = slab['to_date']

                    # dispatched_total = 0
                    # prev_end = None
                    # if item.enable_875_rule or item.enable_75_rule:                                
                    #     outward_items = sorted(outward_items, key=lambda x: getdate(x["date"]))                      
                        
                    #     current_start_date = max(arrival_date if not prev_end else prev_end + timedelta(days=1), first_day)
                    #     slabs = []

                    #     final_outward_date = max(getdate(r["date"]) for r in outward_items)                                                       
                    #     final_invoice_date = min(
                    #         max(final_outward_date, arrival_date + timedelta(days=(item.minimum_commitmentnoofdays or 0) - 1)),
                    #         end_of_month
                    #     )
                    #     duration_days = (final_invoice_date - arrival_date).days + 1
                    #     effective_days = max(duration_days, (item.minimum_commitmentnoofdays or 0))

                    #     for idx, row in enumerate(outward_items):
                    #         current_date = getdate(row["date"])
                        
                    #         dispatched_before_current = dispatched_total   
                    #         dispatched_total += row["qty"]
                    #         dispatched_percent = (dispatched_before_current / inward_qty) * 100 if inward_qty else 0

                            
                    #         if item.enable_875_rule and dispatched_percent >= 87.5:
                    #             rate = item.after_875discounted_rate
                    #             slab_type = "87.5"
                    #         elif item.enable_75_rule and dispatched_percent >= 75:
                    #             rate = item.after_75_discounted_rate
                    #             slab_type = "75"
                    #         else:
                    #             rate = item.rate
                    #             slab_type = "normal"
                            
                    #         if idx + 1 < len(outward_items):
                    #             next_date = getdate(outward_items[idx]["date"])
                    #         else:
                    #             next_date = final_invoice_date
                            
                    #         if next_date < current_start_date:
                    #             continue

                    #         slabs.append({
                    #             "from_date": current_start_date,
                    #             "to_date": next_date,
                    #             "rate": rate,
                    #             "slab_type": slab_type,                                
                    #         })

                    #         current_start_date = next_date + timedelta(days=1)
                    #         outward = frappe.get_doc("Outward Entry", row["parent"])
                    #         outward.billed = 1
                    #         outward.save()
                    
                    #     item_name = frappe.get_value("Item", item.service_type, "item_name")

                    #     merged_slabs = []
                    #     for slab in slabs:
                    #         if not merged_slabs:
                    #             merged_slabs.append(slab)
                    #         else:
                    #             last = merged_slabs[-1]
                    #             # Merge if rate and slab_type match and dates are contiguous
                    #             if slab["rate"] == last["rate"] and slab["slab_type"] == last["slab_type"] and slab["from_date"] == last["to_date"] + timedelta(days=1):
                    #                 # Extend last slab's to_date
                    #                 last["to_date"] = slab["to_date"]
                    #             else:
                    #                 merged_slabs.append(slab)

                    #     for slab in merged_slabs:
                    #         slab_days = (slab["to_date"] - slab["from_date"]).days + 1
                    #         invoice_items.append({
                    #             "item_code": item.service_type,
                    #             "item_name": item_name,
                    #             "rate": slab["rate"],
                    #             "qty": slab_days,
                    #             "uom": "Day",
                    #             "description": f"From {slab['from_date'].strftime('%d-%m-%Y')} to {slab['to_date'].strftime('%d-%m-%Y')}",
                    #             "income_account": income_account,
                    #             "custom_bill_from_date": slab["from_date"],
                    #             "custom_bill_to_date": slab["to_date"],
                    #             "custom_container": container,
                    #             "custom_container_name": container_name,
                    #             "custom_container_status": "Completed" if dispatched_total >= inward_qty else "Partial",
                    #             "custom_invoice_type": "Monthly Billing",
                    #             "custom_outward_qty": dispatched_total
                    #         })
                    #         all_dates.extend([slab['from_date'], slab['to_date']])
                    #         prev_end = slab['to_date'] 

                    if not item.enable_875_rule and not item.enable_75_rule:
                        final_outward_date = max(getdate(r["date"]) for r in outward_items)
                        dispatched_total = sum(r["qty"] for r in outward_items if r.get("qty"))
                        actual_last_outward_date = final_outward_date
                    
                        if (final_outward_date - arrival_date).days < (item.minimum_commitmentnoofdays or 0):
                            display_last_outward_date = arrival_date + timedelta(days=(item.minimum_commitmentnoofdays or 0) - 1)
                        else:
                            display_last_outward_date = final_outward_date

                        duration_days = (actual_last_outward_date - arrival_date).days + 1
                        effective_days = max(duration_days, (item.minimum_commitmentnoofdays or 0))

                        description = f"From {arrival_date.strftime('%d-%m-%Y')} to {display_last_outward_date.strftime('%d-%m-%Y')}"
                        item_name = frappe.get_value("Item", item.service_type, "item_name")
                        invoice_items.append({
                            "item_code": item.service_type,
                            "item_name": item_name,
                            "rate": item.rate,
                            "qty": effective_days,
                            "uom": "Day",
                            "description": description,
                            "income_account": income_account,
                            "custom_bill_from_date": arrival_date,
                            "custom_bill_to_date": display_last_outward_date,
                            "custom_container": container,
                            "custom_container_name": container_name,
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
                            dispatched_percent = (dispatched_total / inward_qty) * 100 if inward_qty else 0

                            if item.enable_875_rule and dispatched_percent >= 87.5:
                                rate = item.after_875discounted_rate
                            elif item.enable_75_rule and dispatched_percent >= 75:
                                rate = item.after_75_discounted_rate
                            else:
                                rate = item.rate
                            item_name = frappe.get_value("Item", item.service_type, "item_name")                            
                            invoice_items.append({
                                "item_code": item.service_type,
                                "item_name": item_name,
                                "qty": duration,
                                "rate": rate,
                                "uom": "Day",
                                "description": f"From {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}",
                                "income_account": income_account,
                                "custom_bill_from_date": start_date,
                                "custom_bill_to_date": end_date,
                                "custom_container": container,
                                "custom_container_name": container_name,
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
                si.custom_invoice_type = "Storage"
                si.custom_consignment = inward.boeinvoice_no
                si.custom_inward_date = inward.sales_invoice_inward_date
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