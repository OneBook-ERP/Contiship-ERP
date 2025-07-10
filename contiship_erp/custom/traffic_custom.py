import frappe

@frappe.whitelist()
def fetch_item_data(service_type):
    try:
        item = frappe.get_doc("Item", service_type)
        result = {
            "container_feet": None,
            "min_commitment": None,
            "square_feet_size":None,
            "ton_size":None,
            # "sqft_type": None,
            "sqft_value": None,            
            "add_on_type":None,
            "custom_add_on_service":None
        }
        if item.custom_rent_type == "Container Based":
            if item.custom_container_feat_size == "20":
                result["container_feet"] = "20"
                result["min_commitment"] = item.custom_container_min_commitment
            elif item.custom_container_feat_size == "40":
                result["container_feet"] = "40"
                result["min_commitment"] = item.custom_container_min_commitment
        elif item.custom_rent_type == "Sqft Based":
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
            if item.custom_add_on_type == "Loading":
                result["add_on_type"] = "Loading"
                result["custom_add_on_service"] = item.custom_add_on_service
            elif item.custom_add_on_type == "Unloading":
                result["add_on_type"] = "Unloading"
                result["custom_add_on_service"] = item.custom_add_on_service
            elif item.custom_add_on_type == "Crossing":
                result["add_on_type"] = "Crossing"
                result["custom_add_on_service"] = item.custom_add_on_service
            
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
