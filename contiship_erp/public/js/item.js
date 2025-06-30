frappe.ui.form.on("Item", {
    custom_container_based_rent(frm){
        if (frm.doc.custom_container_based_rent){
            frm.set_df_property('custom_sqft_based_rent', 'hidden', 1)
        }
        else{
            frm.set_df_property('custom_sqft_based_rent', 'hidden', 0)
        }
    },
    custom_sqft_based_rent(frm){
        if (frm.doc.custom_sqft_based_rent){
            frm.set_df_property('custom_container_based_rent', 'hidden', 1)
        }
        else{
            frm.set_df_property('custom_container_based_rent', 'hidden', 0)
        }
    },
    custom_ton_sqft(frm){
        if (frm.doc.custom_ton_sqft){
            frm.set_df_property('custom_container_sqft', 'hidden', 1)
        }
        else{
            frm.set_df_property('custom_container_sqft', 'hidden', 0)
        }
    },
    custom_container_sqft(frm){
        if (frm.doc.custom_container_sqft){
            frm.set_df_property('custom_ton_sqft', 'hidden', 1)
        }
        else{
            frm.set_df_property('custom_ton_sqft', 'hidden', 0)
        }
    },
    custom_80_ton(frm){
        if (frm.doc.custom_80_ton){
            frm.set_df_property('custom_40_ton', 'hidden', 1)
        }
        else{
            frm.set_df_property('custom_40_ton', 'hidden', 0)
        }
    },
    custom_40_ton(frm){
        if (frm.doc.custom_40_ton){
            frm.set_df_property('custom_80_ton', 'hidden', 1)
        }
        else{
            frm.set_df_property('custom_80_ton', 'hidden', 0)
        }
    },
    custom_20_ft(frm){
        if (frm.doc.custom_20_ft){
            frm.set_df_property('custom_40_ft', 'hidden', 1)
        }
        else{
            frm.set_df_property('custom_40_ft', 'hidden', 0)
        }
    },
    custom_40_ft(frm){
        if (frm.doc.custom_40_ft){
            frm.set_df_property('custom_20_ft', 'hidden', 1)
        }
        else{
            frm.set_df_property('custom_20_ft', 'hidden', 0)
        }
    }
});