import frappe

@frappe.whitelist()
def fetch_item_data(service_type):
    try:
        item = frappe.get_doc("Item", service_type)
        result = {
            "container_feet": None,
            "min_commitment": None
        }
        
        if item.custom_container_based_rent == 1:
            if item.custom_20_ft == 1:
                result["container_feet"] = "20"
            elif item.custom_40_ft == 1:
                result["container_feet"] = "40"
            result["min_commitment"] = item.custom_container_min_commitment

        elif item.custom_sqft_based_rent == 1 :
            # if iy
            pass
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error fetching item data: {str(e)}")
        frappe.throw(f"Error fetching item data: {str(e)}")