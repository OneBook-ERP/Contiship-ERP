$(document).ready(function () {

    hide_default_sidebar();
   
    let home_page = "";
    let toggle_default_sidebar = false;

    // Fetch sidebar configuration
    frappe.call({
        method: "contiship_erp.custom.traffic_custom.get_sidebar_items",
        callback: function (r) {
            if (!r.message || !r.message.enabled) return;

            if (r.message.toggle_default_sidebar == 1) {
                toggle_default_sidebar = true;
                hide_default_sidebar();
            }

            home_page = r.message.home_page || "/app";

            init_custom_sidebar(r.message.items, r.message.brand_logo, r.message.brand_name);
        }
    });
    // Hide default sidebar on load and route change
    
    frappe.router.on("change", hide_default_sidebar);
    window.addEventListener("beforeunload", hide_default_sidebar);

    // Initialize custom sidebar
    function init_custom_sidebar(items, brandLogo, brandName) {
        add_custom_sidebar(items, brandLogo, brandName);
        set_active_link();

        // Handle click + active highlight
        $('#custom-sidebar').off('click.active').on('click.active', '.fs-sidebar-link', function () {
            $('#custom-sidebar .fs-sidebar-link').removeClass('active');
            $(this).addClass('active');
            const menu = $(this).closest('.fs-sidebar-menu');
            menu.show();
            menu.prev('.fs-sidebar-section').removeClass('collapsed');

            if (window.innerWidth <= 768) {
                $('#custom-sidebar').removeClass('active');
            }
        });
    }

    // Build sidebar DOM
    function add_custom_sidebar(items, brandLogo, brandName) {
        if ($('#custom-sidebar').length) return;

        $('body').append(`
            <div id="custom-sidebar" class="fs-sidebar">
                <div class="fs-sidebar-header">                    
                    <span>Contiship</span>
                </div>
                <div class="fs-sidebar-body" id="sidebar-sections"></div>
                
            </div>
            <button id="fs-sidebar-toggle-btn"><i class="fas fa-align-left"></i></button>
        `);

        const container = $('#sidebar-sections');
        const topLevel = items.filter(i => !i.parent_item);

        // Top-level
        topLevel.forEach(item => {
            if (!item.redirect_url) return;
            container.append(`
                <ul class="fs-sidebar-menu">
                    <li>
                        <a href="${item.redirect_url}" class="fs-sidebar-link">
                            <i class="${item.icon || 'fas fa-circle'}"></i> <span>${item.label}</span>
                        </a>
                    </li>
                </ul>
            `);
        });

        // Grouped sections
        const grouped = {};
        items.forEach(i => {
            if (i.parent_item) {
                (grouped[i.parent_item] = grouped[i.parent_item] || []).push(i);
            }
        });

        Object.keys(grouped).forEach(parent => {
            const sectionId = parent.toLowerCase().replace(/\s+/g, '-') + "-menu";
            container.append(`
                <div class="fs-sidebar-section" data-target="#${sectionId}">
                    <span>${parent}</span><span class="fs-toggle-icon"><i class="fa fa-chevron-down"></i></span>
                </div>
                <ul id="${sectionId}" class="fs-sidebar-menu"></ul>
            `);

            grouped[parent].forEach(item => {
                $("#" + sectionId).append(`
                    <li>
                        <a href="${item.redirect_url}" class="fs-sidebar-link">
                            <i class="${item.icon || 'fas fa-circle'}"></i> <span>${item.label}</span>
                        </a>
                    </li>
                `);
            });

            $("#" + sectionId).show();
        });

        // Collapsible sections
        $('.fs-sidebar-section').on('click', function() {
            const target = $(this).data('target');
            $(target).slideToggle(200);
            $(this).toggleClass('collapsed');
        });

        // Mobile toggle
        $('#fs-sidebar-toggle-btn').on('click', function() {
            $('#custom-sidebar').toggleClass('active');
        });
    }

    // Normalize and highlight active link
    function normalizePath(path) {
        if (!path) return '/';
        path = path.split('?')[0].split('#')[0];
        path = decodeURI(path);
        if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
        return path;
    }

    function set_active_link() {
        const current = normalizePath(window.location.pathname);
        $('#custom-sidebar .fs-sidebar-link').removeClass('active');
        $('#custom-sidebar .fs-sidebar-link').each(function () {
            const href = normalizePath($(this).attr('href'));
            if (current === href || current.startsWith(href + '/')) {
                $(this).addClass('active');
                $(this).closest('.fs-sidebar-menu').show();
                $(this).closest('.fs-sidebar-menu').prev('.fs-sidebar-section').removeClass('collapsed');
            }
        });
    }

    // Reapply active on route or navigation change
    $(document).on('page-change', set_active_link);
    $(window).on('popstate hashchange', set_active_link);
});

function hide_default_sidebar() {
    localStorage.setItem("show_sidebar", false);
    setTimeout(function () {
        var route = frappe.get_route() || [];
        if (route[0] == "Workspaces" || route[0] == "List" || (route[0] == "Form" && cur_frm && cur_frm.is_new())) {
            $('.sidebar-toggle-btn').hide();
        } else {
            $('.sidebar-toggle-btn').show();
        }
    }, 10);
}
