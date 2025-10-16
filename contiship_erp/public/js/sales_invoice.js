frappe.listview_settings['Sales Invoice'] = {
    onload: function(listview) {     
        setTimeout(function() {     
            $('button.btn-paging[data-value="2500"]').click();
        }, 500);
    }
};
