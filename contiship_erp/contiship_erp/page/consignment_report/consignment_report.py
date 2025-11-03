from frappe.utils import cint, now_datetime, getdate, flt, formatdate
import frappe
import json
from frappe import _


@frappe.whitelist()
def get_consignment_report_data(filters):
    """
    Fetches report data based on the selected filters and report type.
    """

    # CRITICAL FIX: Convert JSON string filters to Python dictionary
    if isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except json.JSONDecodeError:
            frappe.throw(_("Invalid JSON format for filters."))

    report_type = filters.get("report_type")
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))
    customer = filters.get("customer")
    consignment_no = filters.get("consignment_no")

    # Validate mandatory fields
    if not all([report_type, from_date, to_date, customer]):
         frappe.throw(_("Report Type, From Date, To Date, and Customer are mandatory."))

    if report_type == "Sales Bill Report":
        return get_sales_bill_report(from_date, to_date, customer, consignment_no)

    elif report_type in ["Live Stock Report", "Closing Stock Report"]:
        return get_stock_report(report_type, from_date, to_date, customer, consignment_no)

    return {"columns": [], "data": []} # Ensure a dictionary is returned


def get_sales_bill_report(from_date, to_date, customer, consignment_no):
    """Fetches data from Sales Invoice and Sales Invoice Item DocTypes."""

    columns = [
        {"label": _("Invoice ID"), "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 120},
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Bill From Date"), "fieldname": "custom_bill_from_date", "fieldtype": "Date", "width": 100},
        {"label": _("Bill To Date"), "fieldname": "custom_bill_to_date", "fieldtype": "Date", "width": 100},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": _("Container No"), "fieldname": "custom_container", "fieldtype": "Data", "width": 100},
        {"label": _("Invoice Type"), "fieldname": "custom_invoice_type", "fieldtype": "Data", "width": 120},
        {"label": _("Billed Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 80},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Net Total"), "fieldname": "base_net_total", "fieldtype": "Currency", "width": 100},
        {"label": _("Tax (IGST/CGST/SGST)"), "fieldname": "total_tax", "fieldtype": "Currency", "width": 120},
        {"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 100},
    ]

    filters = {
        "docstatus": 1,
        "posting_date": ["between", [from_date, to_date]],
        "customer": customer,
    }

    if consignment_no:
        invoice_names = frappe.db.get_all(
            "Sales Invoice Item",
            filters={"custom_container": ["like", f"%{consignment_no}%"]},
            pluck="parent",
            distinct=True,
        )
        if not invoice_names:
            return {"columns": columns, "data": []}

        filters["name"] = ["in", invoice_names]

    invoices = frappe.get_list(
        "Sales Invoice",
        filters=filters,
        fields=[
            "name",
            "posting_date",
            "customer_name",
            "base_net_total",
            "total_taxes_and_charges",
            "grand_total",
            "custom_bill_from_date",
            "custom_bill_to_date",
        ],
        order_by="posting_date desc",
        limit_page_length=500,
    )

    invoice_names = [inv.name for inv in invoices]

    if not invoice_names:
        return {"columns": columns, "data": []}

    items = frappe.get_list(
        "Sales Invoice Item",
        filters={"parent": ["in", invoice_names]},
        fields=[
            "parent",
            "item_name",
            "qty",
            "rate",
            "custom_container",
            "custom_invoice_type",
            "igst_amount",
            "cgst_amount",
            "sgst_amount",
            "cess_amount",
        ],
    )

    item_map = frappe._dict()
    for item in items:
        item_map.setdefault(item.parent, []).append(item)

    final_data = []

    for inv in invoices:
        related_items = item_map.get(inv.name, [])
        if related_items:
            for item in related_items:
                total_tax = flt(item.igst_amount) + flt(item.cgst_amount) + flt(item.sgst_amount) + flt(item.cess_amount)
                final_data.append(
                    {
                        "name": inv.name,
                        "posting_date": inv.posting_date,
                        "custom_bill_from_date": inv.custom_bill_from_date,
                        "custom_bill_to_date": inv.custom_bill_to_date,
                        "customer_name": inv.customer_name,
                        "item_name": item.item_name,
                        "custom_container": item.custom_container,
                        "custom_invoice_type": item.custom_invoice_type,
                        "qty": item.qty,
                        "rate": item.rate,
                        "base_net_total": flt(item.qty) * flt(item.rate),
                        "total_tax": total_tax,
                        "grand_total": (flt(item.qty) * flt(item.rate)) + total_tax,
                    }
                )
        else:
            final_data.append(
                {
                    "name": inv.name,
                    "posting_date": inv.posting_date,
                    "custom_bill_from_date": inv.custom_bill_from_date,
                    "custom_bill_to_date": inv.custom_bill_to_date,
                    "customer_name": inv.customer_name,
                    "item_name": _("N/A"),
                    "base_net_total": inv.base_net_total,
                    "grand_total": inv.grand_total,
                    "total_tax": inv.total_taxes_and_charges,
                }
            )

    return {"columns": columns, "data": final_data}


# --- STOCK REPORT LOGIC (FIXED COLUMNS) ---
def get_stock_report(report_type, from_date, to_date, customer, consignment_no):
    """Fetches Live or Closing Stock data using efficient SQL joins and subqueries."""

    columns = [
        {"label": _("Inward Entry ID"), "fieldname": "id", "fieldtype": "Link", "options": "Inward Entry", "width": 150},
        {"label": _("Consignment BOE/Invoice No"), "fieldname": "boeinvoice_no", "fieldtype": "Data", "width": 130},
        {"label": _("Arrival Date"), "fieldname": "container_arrival_date", "fieldtype": "Date", "width": 110},
        {"label": _("Container No"), "fieldname": "container", "fieldtype": "Data", "width": 130},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Inward Qty"), "fieldname": "inward_qty", "fieldtype": "Int", "width": 100},
        {"label": _("Outward Qty"), "fieldname": "outward_qty", "fieldtype": "Int", "width": 100},
        {"label": _("Available Qty"), "fieldname": "available_qty", "fieldtype": "Int", "width": 100},
        {"label": _("Outward History"), "fieldname": "outward_entry_id", "fieldtype": "Data", "width": 250, "formatter": "HTML"},
        {"label": _("Sales Invoice"), "fieldname": "sales_invoice", "fieldtype": "Data", "width": 200, "formatter": "HTML"},
    ]

    conditions = ""
    # Initialize values dict with the mandatory date range
    values = {
        "from_date": from_date,
        "to_date": to_date
    }

    if customer:
        conditions += " AND ie.customer = %(customer)s"
        values["customer"] = customer

    if consignment_no:
        conditions += " AND (ie.boeinvoice_no LIKE %(consignment_no)s OR ied.container LIKE %(consignment_no)s)"
        values["consignment_no"] = f"%{consignment_no}%"

    # --- THIS IS THE FIX ---
    # Filter the main Inward Entry query by arrival date for ALL stock report types
    conditions += " AND ie.arrival_date BETWEEN %(from_date)s AND %(to_date)s"
    # --- END OF FIX ---

    date_filter_sql = ""
    if report_type == "Closing Stock Report":
        # For subqueries: only count outward entries up to the to_date
        date_filter_sql = " AND oe.date <= %(to_date)s"
        columns[8]["label"] = _(f"Available Qty (as of {formatdate(to_date)})")
    
    elif report_type == "Live Stock Report":
        # For subqueries: count all outward entries (no date filter)
        date_filter_sql = "" 
        columns[8]["label"] = _("Available Qty (Live)")

    # This condition is for the main query, to only show rows with stock > 0
    # It also respects the date_filter_sql for closing stock calculations
    availability_condition = f"""
        AND CAST(ied.qty - IFNULL((
            SELECT SUM(oed.qty)
            FROM `tabOutward Entry Items` AS oed
            JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
            WHERE 
                oe.consignment = ie.name 
                AND oed.item = ied.item
                AND oed.container = ied.name
                AND IFNULL(oed.grade, '') = IFNULL(ied.grade, '')
                {date_filter_sql}  
        ), 0) AS UNSIGNED) > 0
    """

    sql_query = f"""
        SELECT
            ie.name AS id,
            ie.boeinvoice_no,
            ied.container,
            ied.container_arrival_date,
            ie.customer,
            ied.item,
            CAST(ied.qty AS UNSIGNED) AS inward_qty,
            CAST(IFNULL((
                SELECT SUM(oed.qty)
                FROM `tabOutward Entry Items` AS oed
                JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
                WHERE 
                    oe.consignment = ie.name 
                    AND oed.item = ied.item
                    AND oed.container = ied.name
                    AND IFNULL(oed.grade, '') = IFNULL(ied.grade, '')
                    {date_filter_sql}
            ), 0) AS UNSIGNED) AS outward_qty,
            CAST(ied.qty - IFNULL((
                SELECT SUM(oed.qty)
                FROM `tabOutward Entry Items` AS oed
                JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
                WHERE 
                    oe.consignment = ie.name 
                    AND oed.item = ied.item
                    AND oed.container = ied.name
                    AND IFNULL(oed.grade, '') = IFNULL(ied.grade, '')
                    {date_filter_sql}
            ), 0) AS UNSIGNED) AS available_qty,
            (
                SELECT GROUP_CONCAT(CONCAT(oe.name, ' (', oed.qty, ')') ORDER BY oe.date DESC SEPARATOR ', ')
                FROM `tabOutward Entry Items` AS oed
                JOIN `tabOutward Entry` AS oe ON oe.name = oed.parent
                WHERE 
                    oe.consignment = ie.name 
                    AND oed.item = ied.item
                    AND oed.container = ied.name
                    AND IFNULL(oed.grade, '') = IFNULL(ied.grade, '')
                    {date_filter_sql}  /* Also apply here for history */
            ) AS outward_entry_id,
            (
                SELECT GROUP_CONCAT(CONCAT(si.name) ORDER BY si.posting_date DESC SEPARATOR ', ')
                FROM `tabSales Invoice` AS si
                WHERE si.custom_reference_docname = ie.name
            ) AS sales_invoice
        FROM
            `tabInward Entry` AS ie
        JOIN
            `tabInward Entry Item` AS ied ON ied.parent = ie.name
        WHERE
            ie.docstatus = 1
            {conditions}
            {availability_condition}
        ORDER BY
            ie.name DESC
    """

    rows = frappe.db.sql(sql_query, values, as_dict=True)

    outward_entries = {}
    for row in rows:
        if row.get("outward_entry_id"):
            if isinstance(row["outward_entry_id"], str):
                for entry_str in row["outward_entry_id"].split(", "):
                    entry_id = entry_str.split(" ")[0]
                    outward_entries[entry_id] = None

    # Get Outward Entry dates for display
    if outward_entries:
        oe_data = frappe.get_list(
            "Outward Entry",
            filters={"name": ["in", list(outward_entries.keys())]},
            fields=["name", "date"],
        )
        outward_date_map = {d["name"]: d["date"] for d in oe_data}
    else:
        outward_date_map = {}

    for row in rows:
        # Reformat Outward History with links and dates
        if row.get("outward_entry_id"):
            entries = []
            if isinstance(row["outward_entry_id"], str):
                for entry_str in row["outward_entry_id"].split(", "):
                    parts = entry_str.split(" ")
                    entry_id = parts[0]
                    qty = parts[-1].strip("()") if parts and len(parts) > 1 and parts[-1].startswith('(') else "N/A"
                    oe_date = outward_date_map.get(entry_id)
                    formatted_date = formatdate(oe_date) if oe_date else "N/A"
                    
                    link = f'<a href="javascript:void(0)" onclick="frappe.set_route(\'Form\', \'Outward Entry\', \'{entry_id}\')">{entry_id}</a> ({qty}) [{formatted_date}]'
                    entries.append(link)
                row["outward_entry_id"] = "<br>".join(entries)
            else:
                row["outward_entry_id"] = ""
        else:
            row["outward_entry_id"] = ""

        # Reformat Sales Invoice Links
        if row.get("sales_invoice"):
            links = [
                f'<a href="javascript:void(0)" onclick="frappe.set_route(\'Form\', \'Sales Invoice\', \'{si.strip()}\')">{si.strip()}</a>'
                for si in row["sales_invoice"].split(",")
            ]
            row["sales_invoice"] = "<br>".join(links)
        else:
            row["sales_invoice"] = ""

    return {"columns": columns, "data": rows}