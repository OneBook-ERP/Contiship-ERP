import frappe
from frappe.model.document import Document

class OutwardEntry(Document):

    def validate(self):
        self.calculate_available_space()

    def calculate_available_space(self):
    
        for row in self.items:
            total_inward = frappe.db.sql_scalar("""
                SELECT SUM(ii.qty)
                  FROM `tabInward Entry Item` ii
                 WHERE ii.consignment = %s
                   AND ii.parent = %s
                   AND docstatus = 1
            """, (row.consignment, row.container)) or 0

            used_outward = frappe.db.sql_scalar("""
                SELECT SUM(oi.qty)
                  FROM `tabOutward Entry Item` oi
                  JOIN `tabOutward Entry` o ON o.name = oi.parent
                 WHERE oi.consignment = %s
                   AND o.docstatus = 1
                   AND o.name != %s
            """, (row.consignment, self.name)) or 0

            available = total_inward - used_outward

            row.available_space = available
