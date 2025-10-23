frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        setTimeout(function() {  
           var navbar = document.getElementById("navbar-breadcrumbs");
            if (navbar) {
                navbar.style.pointerEvents = "none";                
            }  
        }, 100);     
         
    }
});
