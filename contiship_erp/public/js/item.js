frappe.ui.form.on("Item", {
    refresh: function(frm) {
        // Set initial visibility for all fields
        // set_initial_visibility(frm);
    },
    
    onload: function(frm) {
        // Also set visibility when form first loads
        // set_initial_visibility(frm);
    }
});

// Set initial visibility for all fields
function set_initial_visibility(frm) {
    // Container based rent
    if (frm.doc.custom_container_based_rent) {
        hide_fields(frm, ['custom_sqft_based_rent', 'custom_add_on_item', 
                         'custom_consignment_container_items', 'custom_container_items']);
    }
    
    // Sqft based rent
    if (frm.doc.custom_sqft_based_rent) {
        hide_fields(frm, ['custom_container_based_rent', 'custom_add_on_item', 
                         'custom_consignment_container_items', 'custom_container_items']);
        frm.set_df_property("custom_sqft_type", "hidden", 0);
    } else {
        frm.set_df_property("custom_sqft_type", "hidden", 1);
    }
    
    // 80 ton / 40 ton toggle
    if (frm.doc.custom_80_ton) {
        frm.set_df_property('custom_40_ton', 'hidden', 1);
    }
    if (frm.doc.custom_40_ton) {
        frm.set_df_property('custom_80_ton', 'hidden', 1);
    }
    
    // 20ft / 40ft toggle
    if (frm.doc.custom_20_ft) {
        frm.set_df_property('custom_40_ft', 'hidden', 1);
    }
    if (frm.doc.custom_40_ft) {
        frm.set_df_property('custom_20_ft', 'hidden', 1);
    }
    
    // Add on item
    if (frm.doc.custom_add_on_item) {
        hide_fields(frm, ['custom_container_based_rent', 'custom_sqft_based_rent', 
                         'custom_consignment_container_items', 'custom_container_items']);
    }
    
    // Consignment container items
    if (frm.doc.custom_consignment_container_items) {
        hide_fields(frm, ['custom_container_based_rent', 'custom_sqft_based_rent', 
                         'custom_add_on_item', 'custom_container_items']);
    }
    
    // Container items
    if (frm.doc.custom_container_items) {
        hide_fields(frm, ['custom_container_based_rent', 'custom_sqft_based_rent', 
                         'custom_add_on_item', 'custom_consignment_container_items']);
    }
}

// Helper function to hide multiple fields
function hide_fields(frm, fields) {
    fields.forEach(function(field) {
        frm.set_df_property(field, 'hidden', 1);
    });
}

// Keep all your existing field change handlers
frappe.ui.form.on("Item", {
    custom_container_based_rent: function(frm) {
        if (frm.doc.custom_container_based_rent) {
            hide_fields(frm, ['custom_sqft_based_rent', 'custom_add_on_item', 
                            'custom_consignment_container_items', 'custom_container_items']);
        } else {
            frm.set_df_property('custom_sqft_based_rent', 'hidden', 0);
            frm.set_df_property('custom_add_on_item', 'hidden', 0);
            frm.set_df_property('custom_consignment_container_items', 'hidden', 0);
            frm.set_df_property('custom_container_items', 'hidden', 0);
        }
    },

    custom_sqft_based_rent: function(frm) {
        if (frm.doc.custom_sqft_based_rent) {
            hide_fields(frm, ['custom_container_based_rent', 'custom_add_on_item', 
                            'custom_consignment_container_items', 'custom_container_items']);
            frm.set_df_property("custom_sqft_type", "hidden", 0);
        } else {
            frm.set_df_property('custom_container_based_rent', 'hidden', 0);
            frm.set_df_property('custom_add_on_item', 'hidden', 0);
            frm.set_df_property('custom_consignment_container_items', 'hidden', 0);
            frm.set_df_property('custom_container_items', 'hidden', 0);
            frm.set_df_property("custom_sqft_type", "hidden", 1);
        }
    },

    custom_80_ton: function(frm) {
        frm.set_df_property('custom_40_ton', 'hidden', frm.doc.custom_80_ton ? 1 : 0);
    },

    custom_40_ton: function(frm) {
        frm.set_df_property('custom_80_ton', 'hidden', frm.doc.custom_40_ton ? 1 : 0);
    },

    custom_20_ft: function(frm) {
        frm.set_df_property('custom_40_ft', 'hidden', frm.doc.custom_20_ft ? 1 : 0);
    },

    custom_40_ft: function(frm) {
        frm.set_df_property('custom_20_ft', 'hidden', frm.doc.custom_40_ft ? 1 : 0);
    },

    custom_add_on_item: function(frm) {
        if (frm.doc.custom_add_on_item) {
            hide_fields(frm, ['custom_container_based_rent', 'custom_sqft_based_rent', 
                            'custom_consignment_container_items', 'custom_container_items']);
        } else {
            frm.set_df_property('custom_container_based_rent', 'hidden', 0);
            frm.set_df_property('custom_sqft_based_rent', 'hidden', 0);
            frm.set_df_property('custom_consignment_container_items', 'hidden', 0);
            frm.set_df_property('custom_container_items', 'hidden', 0);
        }
    },

    custom_consignment_container_items: function(frm) {
        if (frm.doc.custom_consignment_container_items) {
            hide_fields(frm, ['custom_rent_type', 'custom_container_feat_size', 
                            'custom_container_min_commitment', 'custom_add_on_type','custom_add_on_service',
                        'custom_square_feet_size','custom_ton_size','custom_sqft_min_commitment','custom_container_items']);
        } else {
            frm.set_df_property('custom_rent_type', 'hidden', 0);
            frm.set_df_property('custom_container_feat_size', 'hidden', 0);
            frm.set_df_property('custom_container_min_commitment', 'hidden', 0);
            frm.set_df_property('custom_add_on_type', 'hidden', 0);
            frm.set_df_property('custom_add_on_service', 'hidden', 0);
            frm.set_df_property('custom_square_feet_size', 'hidden', 0);
            frm.set_df_property('custom_ton_size', 'hidden', 0);
            frm.set_df_property('custom_sqft_min_commitment', 'hidden', 0);
            frm.set_df_property('custom_container_items', 'hidden', 0);
        }
    },

    custom_container_items: function(frm) {
        if (frm.doc.custom_container_items) {
            hide_fields(frm, ['custom_rent_type', 'custom_container_feat_size', 
                'custom_container_min_commitment', 'custom_add_on_type','custom_add_on_service',
            'custom_square_feet_size','custom_ton_size','custom_sqft_min_commitment','custom_consignment_container_items']);
        } else {
            frm.set_df_property('custom_rent_type', 'hidden', 0);
            frm.set_df_property('custom_container_feat_size', 'hidden', 0);
            frm.set_df_property('custom_container_min_commitment', 'hidden', 0);
            frm.set_df_property('custom_add_on_type', 'hidden', 0);
            frm.set_df_property('custom_add_on_service', 'hidden', 0);
            frm.set_df_property('custom_square_feet_size', 'hidden', 0);
            frm.set_df_property('custom_ton_size', 'hidden', 0);
            frm.set_df_property('custom_sqft_min_commitment', 'hidden', 0);
            frm.set_df_property('custom_consignment_container_items', 'hidden', 0);
        }
    }
});