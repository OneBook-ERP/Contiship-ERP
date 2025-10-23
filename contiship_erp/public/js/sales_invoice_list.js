frappe.listview_settings['Sales Invoice'] = {
    onload: function(listview) {     
        setTimeout(function() {     
            $('button.btn-paging[data-value="2500"]').click();
            if (window.location.pathname.includes('sales-invoice')) {
                listview.filter_area.add([[ 'Sales Invoice', 'docstatus', '=', 0 ]]);
                listview.refresh();
            }
        }, 500);
    }
};
