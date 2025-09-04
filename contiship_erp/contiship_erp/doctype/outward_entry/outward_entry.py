import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days
from frappe.utils import formatdate
from datetime import datetime, timedelta



class OutwardEntry(Document):

    def validate(self):
        self.calculate_available_space()       

    def on_submit(self):        
        frappe.enqueue("contiship_erp.contiship_erp.doctype.outward_entry.outward_entry.create_container_sales_invoice", queue='default', job_name=f"Create Sales Invoice for {self.name}", outward_entry=self.name)
   
    def calculate_available_space(self):
        errors = []

        outward_date = getdate(self.date) if self.date else None

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

            arrival_date = frappe.db.get_value(
                "Inward Entry Item",
                {"name": row.container, "item": row.item},
                "container_arrival_date"
            )

            if arrival_date:
                arrival_date = getdate(arrival_date)
                if outward_date and outward_date < arrival_date:
                    errors.append(f"""
                        <b>Container:</b> {row.container}<br>
                        <b>Item:</b> {row.item}<br>
                        <b>Arrival Date:</b> {arrival_date}<br>
                        <b>Outward Date:</b> {outward_date}<br>
                        <b style='color:red;'>Error:</b> Outward date cannot be earlier than arrival date.<br><hr>
                    """)

        if errors:
            frappe.throw(
                "<b>Outward Entry has issues:</b><br><br>" + "".join(errors),
                title="Outward Entry Validation Failed"
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
            iei.item, iei.qty, iei.uom, iei.grade_item, iei.grade, iei.crossing_item,
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
        "grade":row.grade,        
    }
   
@frappe.whitelist()
def get_all_inward_items(consignment):
    if not consignment:
        return []

    result = frappe.db.sql("""
        SELECT 
            iei.name,
            iei.container,
            iei.item,
            iei.qty,
            iei.uom,
            iei.grade_item,
            iei.grade,
            iei.crossing_item,
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
        ORDER BY iei.idx ASC
    """, {
        "consignment": consignment
    }, as_dict=True)


    items = []
    for row in result:
        used = row.used_qty or 0
        remaining_qty = row.qty - used

        if remaining_qty > 0:
            items.append({
                "name": row.name,
                "container": row.container,
                "item": row.item,
                "qty": remaining_qty,
                "uom": row.uom,
                "grade_item": row.grade_item,
                "grade": row.grade,
                "crossing_item": row.crossing_item
            })

    return items

@frappe.whitelist()
def get_inward_html_table(customer):
    entries = frappe.get_all(
        "Inward Entry",
        filters={"customer": customer, "invoice_generated": 0, "docstatus": 1},
        fields=["name", "arrival_date", "docstatus", "boeinvoice_no"]
    )

    if not entries:
        return "<p class='text-muted'>No Inward Entries found for this customer.</p>"

    html = """
    <style>
        .inward-table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 20px;
            font-size: 13px;
        }
        .inward-table th, .inward-table td {
            border: 1px solid #444;
            padding: 6px 8px;
            text-align: left;
        }
        .inward-table th {
            background-color: #f4f4f4;
            font-weight: 600;
        }
        .inward-table .nested-table th {
            background-color: #fafafa;
            font-weight: 500;
        }
        .inward-table .nested-table {
            border-collapse: collapse;
            width: 100%;
            margin: 0;
        }
        .inward-table .nested-table td, 
        .inward-table .nested-table th {
            border: 1px solid #ccc;
            padding: 4px 6px;
            font-size: 12px;
        }
    </style>
    <div class="table-responsive">
        <table class="inward-table">
            <thead>
                <tr>
                    <th style="width: 10%;">Inward ID</th>
                    <th style="width: 10%;">BOE Invoice</th>
                    <th style="width: 8%;">Date</th>
                    <th style="width: 6%;">Status</th>
                    <th>Items</th>
                </tr>
            </thead>
            <tbody>
    """

    for entry in entries:
        item_rows = ""
        has_available_item = False

        inward_items = frappe.get_all(
            "Inward Entry Item",
            filters={"parent": entry.name},
            fields=["name", "item", "qty", "uom", "grade_item", "grade", "container", "container_arrival_date","crossing_item","idx"],
            order_by="idx asc"
        )

        for item in inward_items:
            used_qty = frappe.db.sql("""
                SELECT SUM(oi.qty)
                FROM `tabOutward Entry Items` oi
                JOIN `tabOutward Entry` o ON o.name = oi.parent
                WHERE o.consignment = %s
                AND oi.container = %s
                AND oi.item = %s
            """, (entry.name, item.name, item.item))[0][0] or 0

            available_qty = item.qty - used_qty

            if available_qty > 0:
                has_available_item = True
                item_rows += f"""
                    <tr>
                        <td>{item.container}</td>
                        <td>{item.item}</td>
                        <td>{formatdate(item.container_arrival_date)}</td>                       
                        <td>{item.grade or ""}</td>
                        <td>{"Yes" if item.crossing_item == 1 else ""}</td>
                        <td>{item.uom or ""}</td>
                        <td style="text-align: right;">{available_qty} / {item.qty}</td>
                    </tr>
                """

        if has_available_item:
            html += f"""
                <tr>
                    <td>{entry.name}</td>
                    <td>{entry.boeinvoice_no or ""}</td>
                    <td>{formatdate(entry.arrival_date)}</td>
                    <td>{"Submitted" if entry.docstatus == 1 else "Draft"}</td>
                    <td>
                        <table class="nested-table">
                            <thead>
                                <tr>
                                    <th>Container</th>
                                    <th>Item</th>
                                    <th>Arrival Date</th>                                  
                                    <th>Grade</th>
                                    <th>Crossing</th>
                                    <th>UOM</th>
                                    <th style="text-align: right;">Available / Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {item_rows}
                            </tbody>
                        </table>
                    </td>
                </tr>
            """

    html += "</tbody></table></div>"
    return html


@frappe.whitelist()
def create_container_sales_invoice(outward_entry):
    try:
        outward = frappe.get_doc("Outward Entry", outward_entry)
        inward = frappe.get_doc("Inward Entry", outward.consignment)
        if inward.service_type == "Sqft Based":
            return

        customer = frappe.get_doc("Customer", outward.customer)
        tariffs = inward.customer_tariff_config or customer.custom_customer_traffic_config

        if not tariffs:
            frappe.error_log("No tariff configuration found.")

        containers_not_fully_outwarded = []
        for item in inward.inward_entry_items:
            if item.crossing_item:
                continue
            container = item.name
            inward_qty = item.qty

            outward_items = frappe.get_all("Outward Entry Items",
                filters={
                    "container": container,
                    "parenttype": "Outward Entry",
                    "docstatus": 1,
                    "crossing_item": 0,
                    "parent": ["!=", outward.name]                    
                },
                fields=["qty"]
            )

            total_outward_qty = sum(out.qty for out in outward_items)
            
            if outward:                
                for row in outward.items:
                    if row.container == container:
                        total_outward_qty += row.qty            

            if total_outward_qty < inward_qty:
                containers_not_fully_outwarded.append(container)                
           
        if containers_not_fully_outwarded:
            frappe.log_error(f"Cannot create invoice. Containers not fully outwarded: {', '.join(containers_not_fully_outwarded)}")
            return

        invoice_items = []

        for item in inward.inward_entry_items:       
            container = item.name
            container_size = item.container_size
            inward_qty = item.qty
            month_invoice_details = get_monthly_invoice(container)
            if month_invoice_details:
                if month_invoice_details["custom_container_status"] == "Completed":
                    continue
                if month_invoice_details["custom_bill_to_date"]:
                    arrival_date = getdate(month_invoice_details["custom_bill_to_date"]) + timedelta(days=1)
            else:
                arrival_date = getdate(item.container_arrival_date)

            tariff = next((
                t for t in tariffs 
                if (
                    (t.rent_type == "Container Based" and str(t.container_feet) == str(container_size)) or
                    (t.rent_type == "LCL" and str(t.lcl_type) == str(container_size))
                )
            ), None)

            if not tariff:
                frappe.log_error(f"No matching tariff for {container_size}ft", f"Tariff Error for {container}")
                continue

            items = frappe.get_all("Outward Entry Items",
                filters={
                    "container": container,
                    "parenttype": "Outward Entry",
                    "crossing_item": 0,                                 
                },
                fields=["qty", "parent"]
            )
            outward_items = []

            for item in items:
                billed = frappe.db.get_value("Outward Entry", item["parent"], "billed")
                if not billed:
                    item["date"] = frappe.db.get_value("Outward Entry", item["parent"], "date")
                    outward_items.append(item)
           
            if not outward_items:
                continue

            outward_items.sort(key=lambda x: x["date"])
            default_company = frappe.defaults.get_user_default("Company")
            income_account = frappe.get_value("Company", default_company, "default_income_account")

            if tariff.enable_875_rule or tariff.enable_75_rule:                           
                outward_items = sorted(outward_items, key=lambda x: getdate(x["date"]))

                dispatched_total = 0
                if month_invoice_details:
                    dispatched_total = get_billed_qty(container)
                
                current_start_date = arrival_date
                slabs = []

                final_outward_date = max(getdate(r["date"]) for r in outward_items)
                duration_days = (final_outward_date - arrival_date).days + 1
                commitment_days = tariff.minimum_commitmentnoofdays if not month_invoice_details else 0
                effective_days = max(duration_days, commitment_days)                                
                if not month_invoice_details and tariff.minimum_commitmentnoofdays:
                    final_invoice_date = max(final_outward_date, arrival_date + timedelta(days=tariff.minimum_commitmentnoofdays - 1))
                else:
                    final_invoice_date = final_outward_date

                for idx, row in enumerate(outward_items):
                    current_date = getdate(row["date"])
                   
                    dispatched_before_current = dispatched_total   
                    dispatched_total += row["qty"]
                    dispatched_percent = (dispatched_before_current / inward_qty) * 100 if inward_qty else 0
                    
                    if tariff.enable_875_rule and dispatched_percent >= 87.5 and (duration_days>commitment_days):
                        rate = tariff.after_875discounted_rate
                        slab_type = "87.5"
                    elif tariff.enable_75_rule and dispatched_percent >= 75 and (duration_days>commitment_days):
                        rate = tariff.after_75_discounted_rate
                        slab_type = "75"
                    else:
                        rate = tariff.rate
                        slab_type = "normal"
                    
                    if idx + 1 < len(outward_items):
                        next_date = getdate(outward_items[idx]["date"])
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
               
                item_name = frappe.get_value("Item", tariff.service_type, "item_name")                
                merged_slabs = []
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
                        "custom_container_status": "Completed",
                        "custom_invoice_type": "Immediate Billing",
                    })


            
            if not tariff.enable_875_rule and not tariff.enable_75_rule:
                final_outward_date = max(getdate(r["date"]) for r in outward_items)
                actual_last_outward_date = final_outward_date
                duration_days = (actual_last_outward_date - arrival_date).days + 1
                commitment_days = tariff.minimum_commitmentnoofdays if not month_invoice_details else 0
                effective_days = max(duration_days, commitment_days) 
                
                if not month_invoice_details and tariff.minimum_commitmentnoofdays:
                    final_invoice_date = max(actual_last_outward_date, arrival_date + timedelta(days=tariff.minimum_commitmentnoofdays - 1))
                else:
                    final_invoice_date = actual_last_outward_date

                description = f"From {arrival_date.strftime('%d-%m-%Y')} to {final_invoice_date.strftime('%d-%m-%Y')}"
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
                    "custom_bill_to_date": final_invoice_date,
                    "custom_container": container,
                    "custom_container_status": "Completed",
                    "custom_invoice_type": "Immediate Billing",
                    
                })

        frappe.log_error("invoice_items", invoice_items)

        if not invoice_items:
            frappe.log_error("No invoice items generated.")

        si = frappe.new_doc("Sales Invoice")
        si.customer = outward.customer
        si.posting_date = frappe.utils.nowdate()
        si.custom_reference_doctype = "Inward Entry"
        si.custom_reference_docname = inward.name
        si.custom_invoice_type = "Immediate Billing"
        si.custom_consignment = inward.boeinvoice_no
        si.set("items", invoice_items)   
        si.insert()

        inward.invoice_generated = 1
        inward.save()
        
        return si.name

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Container Invoice Generation Failed")
        frappe.throw("An error occurred while generating the container invoice.")


def get_monthly_invoice(container):
    try:
        frappe.log_error("row", container)

        invoice_items = frappe.get_all(
            "Sales Invoice Item",
            filters={
                "custom_container": container,
                "parenttype": "Sales Invoice",
                "custom_invoice_type": "Monthly Billing"
            },
            fields=["name", "creation", "custom_bill_from_date", "custom_bill_to_date","custom_container_status"],
            order_by="creation desc",
            limit=1
        )

        if invoice_items:
            return invoice_items[0]
        else:
            return None

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_monthly_invoice error")
        return None


    
def get_billed_qty(container):
    try:
        items = frappe.get_all(
            "Outward Entry Items",
            filters={
                "container": container,
                "parenttype": "Outward Entry",
                "crossing_item": 0,
            },
            fields=["qty", "parent"]
        )

        total_qty = 0

        for item in items:
            billed = frappe.db.get_value("Outward Entry", item["parent"], "billed")
            if billed:
                total_qty += item["qty"] or 0

        return total_qty

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_billed_qty error")
        return 0

