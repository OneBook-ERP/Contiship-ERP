import frappe

@frappe.whitelist()
def fetch_item_data(service_type):
    try:
        item = frappe.get_doc("Item", service_type)
        result = {
            "container_feet": None,
            "min_commitment": None,
            # "sqft_type": None,
            "sqft_value": None
        }
        
        if item.custom_container_based_rent == 1:
            if item.custom_20_ft == 1:
                result["container_feet"] = "20"
            elif item.custom_40_ft == 1:
                result["container_feet"] = "40"
            result["min_commitment"] = item.custom_container_min_commitment

        elif item.custom_sqft_based_rent == 1:
            result["sqft_type"] = item.custom_sqft_type
            
            if item.custom_sqft_type == "Ton Based":
                if item.custom_80_ton == 1:
                    result["sqft_value"] = "80 Ton"
                    result["ton_sqft"] = item.custom_ton_based_sqft
                    result["min_commitment"] = item.custom_sqft_min_commitment
                elif item.custom_40_ton == 1:
                    result["sqft_value"] = "40 Ton"
                    result["ton_sqft"] = item.custom_ton_based_sqft
                    result["min_commitment"] = item.custom_sqft_min_commitment
                
            elif item.custom_sqft_type == "Container Based" :
                result["sqft_value"] = "Container"
                result["container_sqft"] = item.custom_container_based_sqft
                result["min_commitment"] = item.custom_sqft_min_commitment
                
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
            custom_container_based_rent = 1
            OR custom_sqft_based_rent = 1
            OR custom_add_on_item = 1
        ) AND ({0} LIKE %s OR item_name LIKE %s)
        ORDER BY idx DESC
        LIMIT %s OFFSET %s
    """.format(searchfield), ('%%%s%%' % txt, '%%%s%%' % txt, page_len, start))