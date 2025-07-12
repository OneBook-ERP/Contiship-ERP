import frappe
from frappe.model.document import Document

class OutwardEntry(Document):

    def validate(self):
        self.calculate_available_space()
        self.create_so()

    # def after_save(self):
    #     self.create_so()

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


    def create_so(self):
        from frappe.utils import getdate
        consignment = frappe.get_doc("Consignment", self.consignment)
        if consignment.invoice_generated:
            frappe.throw("Invoice Already Created for this Cosignment")
            return
        today = getdate()
        traffic_config = []

        if consignment.customer_traffic_config:
            traffic_config = consignment.customer_traffic_config
        elif consignment.customer:
            customer = frappe.get_doc("Customer", consignment.customer)
            traffic_config = customer.customer_traffic_config
        else:
            frappe.throw("Customer Traffic Config not found")
        
        all_completed = True
        for container in consignment.container_entry:
            total_inward = frappe.db.sql("""
                SELECT SUM(ii.qty)
                FROM `tabInward Entry Item` ii
                JOIN `tabInward Entry` ie ON ie.name = ii.parent
                WHERE ie.consignment = %s AND ie.container = %s
            """, (self.consignment, container.name))[0][0] or 0

            used_outward = frappe.db.sql("""
                SELECT SUM(oi.qty)
                FROM `tabOutward Entry Items` oi
                JOIN `tabOutward Entry` o ON o.name = oi.parent
                WHERE o.consignment = %s AND o.container = %s
            """, (self.consignment, container.name))[0][0] or 0

            if total_inward != used_outward:
                all_completed = False
                break
        frappe.log_error("All Completed: " + str(all_completed))

        if not all_completed:            
            return

        
        matching_items = []
        total_con_size_ft = 0
        sqft_rate = 0
        sqft_min_days = 0
        sqft_service = None
        square_feet_size = None

        for item in consignment.container_entry:
            arrival_date = getdate(item.container_arrival_date)
            days_stayed = (today - arrival_date).days
            days_stayed = days_stayed if days_stayed > 0 else 1

            for traffic in traffic_config:
                service_item = frappe.get_doc("Item", traffic.service_type)

                if service_item.custom_rent_type == "Container Based":
                    if item.container_size == service_item.custom_container_feat_size:
                        rate = traffic.rate
                        min_commitment = traffic.minimum_commitmentnoofdays or 1
                        duration_days = max(days_stayed, min_commitment)

                        matching_items.append({
                            "item_code": item.containers,
                            "qty": 1,
                            "uom": "Day",
                            "rate": rate * duration_days,
                            "description": f"{item.container_size}ft container x {duration_days} days (min {min_commitment})"
                        })

                elif service_item.custom_rent_type == "Sqft Based":
                    sqft_service = traffic.service_type
                    square_feet_size = int(traffic.square_feet_size)
                    sqft_rate = traffic.rate
                    sqft_min_days = traffic.minimum_commitmentnoofdays or 1
                    total_con_size_ft += (int(item.container_size or 0))*10

                    if sqft_service and total_con_size_ft > 0:
                        frappe.log_error("Total Con Size FT: ",total_con_size_ft)
                        frappe.log_error("square_feet_size: ",square_feet_size)             
                        duration_days = max(days_stayed, sqft_min_days)

                        if total_con_size_ft <= square_feet_size:
                            matching_items.append({
                                "item_code": sqft_service,
                                "qty": 1,
                                "rate": sqft_rate * duration_days,
                                "description": f"1 block for {total_con_size_ft} sqft x {duration_days} days (min {sqft_min_days})"
                            })
                        else:              

                            extra_sqft = total_con_size_ft - square_feet_size
                            if extra_sqft > 0:
                                if extra_sqft > 500:
                                    # Use 1000 sqft again
                                    matching_items.append({
                                        "item_code": sqft_service,
                                        "qty": 1,
                                        "rate": sqft_rate * duration_days,
                                        "description": f"Extra 1000 sqft block for {extra_sqft} sqft x {duration_days} days"
                                    })
                                else:
                                    # Use 500 sqft item
                                    sqft_500_item = frappe.get_all(
                                        "Item",
                                        filters={
                                            "custom_rent_type": "Sqft Based",
                                            "custom_square_feet_size": 500
                                        },
                                        fields=["name"],
                                        limit=1
                                    )
                                    if not sqft_500_item:
                                        frappe.throw("No Sqft Based item configured for 500 sqft blocks.")

                                    sqft_500_item_code = sqft_500_item[0].name

                                    price_data = frappe.db.get_value(
                                        "Item Price",
                                        {
                                            "item_code": sqft_500_item_code,
                                            "price_list": "Standard Selling",
                                            "selling": 1
                                        },
                                        ["price_list_rate", "valid_from", "valid_upto"],
                                        as_dict=True
                                    )
                                    if not price_data:
                                        frappe.throw(f"No price found for 500 sqft service item: {sqft_500_item_code}")

                                    valid_from = getdate(price_data.valid_from) if price_data.valid_from else None
                                    valid_upto = getdate(price_data.valid_upto) if price_data.valid_upto else None
                                    today = getdate()
                                    if (valid_from and today < valid_from) or (valid_upto and today > valid_upto):
                                        frappe.throw(
                                            f"Price for item '{sqft_500_item_code}' is not valid on {today}. "
                                            f"Valid from {valid_from} to {valid_upto}."
                                        )
                                    rate_for_500_sqft = price_data.price_list_rate
                                    matching_items.append({
                                        "item_code": sqft_500_item_code,
                                        "qty": 1,
                                        "rate": rate_for_500_sqft * duration_days,
                                        "uom": "Day",
                                        "description": f"1 block for extra {extra_sqft} sqft x {duration_days} days"
                                    })


        if not matching_items:
            frappe.throw(f"No matching items found for consignment {self.consignment}.")
       
        invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": consignment.customer,
            "posting_date": today,
            "items": matching_items
        })
        invoice.insert()
        consignment.invoice_generated = 1
        consignment.final_invoice_link = invoice.name
        consignment.save()
        frappe.msgprint(f"Sales Invoice <a href='/app/sales-invoice/{invoice.name}'>{invoice.name}</a> created automatically.")




@frappe.whitelist()
def get_arrival_date(consignment, name):
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


  