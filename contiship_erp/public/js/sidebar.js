$(document).ready(function () { 


    $('.layout-side-section, .sidebar-toggle-btn').hide(); 

    let home_page = "";

    frappe.call({
        method: "contiship_erp.custom.traffic_custom.get_sidebar_items",
        callback: function (r) {
            if (!r.message || !r.message.enabled) {
                return;
            }
            if (r.message.toggle_default_sidebar == 1) {
                hide_default_sidebar();
            }
            if (r.message.home_page) {
                home_page = r.message.home_page;
            }else{
                home_page = "/app";
            }
            init_custom_sidebar(r.message.items);
        }
    });

    function hide_default_sidebar() {
        let retryCount = 0; 
        const maxRetries = 5; 

        function handleSidebar() {
            const route = frappe.get_route();
            if (!route || !route.length) {
                setTimeout(handleSidebar, 200);
                return;
            }    
            
            $(document.body).trigger("toggleSidebar", { force_hide: true });
            
            if (route[0] === "List" || route[0] === "Workspaces") {
                $(document.body).trigger("toggleSidebar", { force_hide: true });
            }
            else if (route[0] === "Form") {
                if (typeof cur_frm === 'undefined' || cur_frm === null || 
                    !cur_frm || !$('.form-layout').length) { 
                    if (retryCount < maxRetries) {
                        retryCount++;
                        setTimeout(handleSidebar, 200);
                        return;
                    } else {
                        $(document.body).trigger("toggleSidebar", { force_hide: true });
                        retryCount = 0; 
                        return;
                    }
                }
                
                retryCount = 0;
                
                if (cur_frm.is_new()) {
                    $(document.body).trigger("toggleSidebar", { force_hide: true });
                } else {
                    $(document.body).trigger("toggleSidebar", { force_show: true });
                }
            }
            else if (route[0] === "print") {
                $(document.body).trigger("toggleSidebar", { force_show: true });
            }
            else {
                $(document.body).trigger("toggleSidebar", { force_hide: true });
            }

            const logo = document.querySelector(".navbar-brand");
            if (logo) {
                logo.setAttribute("href", home_page);
            }
        }   
       
        $(document.body).on("toggleSidebar", (e, opts = {}) => {
            let sidebar_wrapper = $(".layout-side-section");
            let sidebar_toggle = $(".sidebar-toggle-btn");
    
            if (opts.force_hide) {
                sidebar_wrapper.hide();
                sidebar_toggle.hide();
            }
            if (opts.force_show) {
                sidebar_wrapper.show();
                sidebar_toggle.show();
            }
        });         

        window.handleSidebar = handleSidebar;

        handleSidebar();
    
        $(document).on("page-change", function () {
            $(document.body).trigger("toggleSidebar", { force_hide: true });
            retryCount = 0; 
            setTimeout(handleSidebar, 100); 
        });
        
        const observer = new MutationObserver(() => {
            clearTimeout(window.sidebarObserverTimeout);
            window.sidebarObserverTimeout = setTimeout(handleSidebar, 150);
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }
    

    function add_custom_sidebar(items) {
        if ($('#custom-sidebar').length === 0) {
            let sidebar_html = `
            <div id="custom-sidebar">
                <h2 class="sidebar-title">Contiship</h2>
                <div id="dynamic-sections"></div>
            </div>
    
            <button id="sidebar-toggle-btn">☰</button>
    
           <style>
                :root { --custom-sidebar-w: 220px; }

                /* ---------- Light Theme ---------- */
                html[data-theme="light"] {
                    --sidebar-bg: linear-gradient(180deg, #1e3a8a 0%, #1d4ed8 100%);
                    --sidebar-text: #ffffff;
                    --sidebar-title: #bfdbfe;
                    --sidebar-link-hover-bg: #2563eb;
                    --sidebar-link-hover-text: #eff6ff;
                    --sidebar-link-active-bg: #3b82f6;
                    --sidebar-section: #93c5fd;
                    --sidebar-btn-bg: #60a5fa;
                    --sidebar-btn-text: #ffffff;
                }

                /* ---------- Dark Theme ---------- */
                html[data-theme="dark"] {
                    --sidebar-bg: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
                    --sidebar-text: #f9fafb;
                    --sidebar-title: #60a5fa;
                    --sidebar-link-hover-bg: #334155;
                    --sidebar-link-hover-text: #f1f5f9;
                    --sidebar-link-active-bg: #475569;
                    --sidebar-section: #94a3b8;
                    --sidebar-btn-bg: #60a5fa;
                    --sidebar-btn-text: #f9fafb;
                }

                /* ---------- Base Sidebar ---------- */
                #custom-sidebar {
                    position: fixed;
                    top: 0; left: 0;
                    width: var(--custom-sidebar-w);
                    height: 100%;
                    background: var(--sidebar-bg);
                    color: var(--sidebar-text);
                    padding: 20px 12px;
                    overflow-y: auto;
                    z-index: 1000;
                    box-shadow: 2px 0 10px rgba(0,0,0,0.25);
                    font-family: 'Verdana', sans-serif;
                    transition: transform 0.3s ease-in-out;
                }
                .sidebar-title {
                    font-size:20px; font-weight:700; margin-bottom:30px;
                    color: var(--sidebar-title);
                }
                .sidebar-link {
                    color: var(--sidebar-text);
                    text-decoration: none;
                    display: flex;
                    align-items: center;
                    padding: 10px 12px;
                    border-radius: 6px;
                    transition: all 0.2s ease-in-out;
                }
                .sidebar-link span { margin-left: 10px; }
                .sidebar-link:hover {
                    background: var(--sidebar-link-hover-bg);
                    color: var(--sidebar-link-hover-text);
                }
                .sidebar-link.active {
                    background: var(--sidebar-link-active-bg);
                    font-weight: 700;
                }

                .sidebar-section {
                    margin-top: 20px; font-size: 13px; font-weight: 600;
                    color: var(--sidebar-section);
                    text-transform: uppercase; cursor: pointer;
                    display: flex; justify-content: space-between;
                }
                .sidebar-menu { list-style:none; padding:0; margin:0; }
                .toggle-icon { font-size: 10px; transition: transform 0.2s ease; }

                /* ---------- Mobile Toggle Button ---------- */
                #sidebar-toggle-btn {
                    position: fixed;
                    top: 8px; left: 12px;
                    background: var(--sidebar-btn-bg);
                    color: var(--sidebar-btn-text);
                    border: none;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 15px;
                    z-index: 1100;
                    display: none;
                }

                @media (min-width: 769px) {
                    html, body { overflow-x: hidden; }
                    body { padding-left: var(--custom-sidebar-w) !important; }
                }

                @media (max-width: 1024px) and (min-width: 769px) {
                    :root { --custom-sidebar-w: 180px; }
                }

                @media (max-width: 768px) {
                    body { padding-left: 0 !important; }
                    #custom-sidebar { transform: translateX(-100%); }
                    #custom-sidebar.active { transform: translateX(0); }
                    #sidebar-toggle-btn { display: block; }
                }
            </style>


            `;
    
            $('body').append(sidebar_html);
    
            // Build menu dynamically
            let container = $("#dynamic-sections");
    
            // 1. Items without parent -> show first
            let topLevel = items.filter(i => !i.parent_item);
            topLevel.forEach(item => {
                container.append(`
                    <ul class="sidebar-menu">
                        <li>
                            <a href="${item.redirect_url || "#"}" class="sidebar-link">
                                ${item.icon || "📄"} <span>${item.label}</span>
                            </a>
                        </li>
                    </ul>
                `);
            });
    
            // 2. Group items by parent
            let grouped = {};
            items.forEach(i => {
                if (i.parent_item) {
                    if (!grouped[i.parent_item]) grouped[i.parent_item] = [];
                    grouped[i.parent_item].push(i);
                }
            });
    
            // 3. Render each parent group
            Object.keys(grouped).forEach(parent => {
                let sectionId = parent.toLowerCase().replace(/\s+/g, '-') + "-menu";
                let section = `
                    <div class="sidebar-section" data-target="#${sectionId}">
                        <span>${parent}</span><span class="toggle-icon">▼</span>
                    </div>
                    <ul id="${sectionId}" class="sidebar-menu"></ul>
                `;
                container.append(section);
    
                let $submenu = $("#" + sectionId);
                grouped[parent].forEach(item => {
                    $submenu.append(`
                        <li>
                            <a href="${item.redirect_url || "#"}" class="sidebar-link">
                                ${item.icon || "📄"} <span>${item.label}</span>
                            </a>
                        </li>
                    `);
                });
            });
    
            // Expand/collapse toggle
            $('#custom-sidebar .sidebar-section').on('click', function () {
                let target = $(this).data('target');
                $(target).slideToggle(200);
                $(this).toggleClass("collapsed");
            });
    
            // Mobile toggle
            $('#sidebar-toggle-btn').on('click', function () {
                $('#custom-sidebar').toggleClass('active');
            });
        }
    }
    

    function normalizePath(path) {
        if (!path) return '/';
        path = path.split('?')[0].split('#')[0];
        path = decodeURI(path);
        if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
        return path;
    }

    function set_active_link() {
        const current = normalizePath(window.location.pathname);
        $('#custom-sidebar .sidebar-link').removeClass('active');
        $('#custom-sidebar .sidebar-link').each(function () {
            const href = normalizePath($(this).attr('href'));
            if (current === href || current.startsWith(href + '/')) {
                $(this).addClass('active');
                const menu = $(this).closest('.sidebar-menu');
                menu.show();
                menu.prev('.sidebar-section').removeClass('collapsed');
            }
        });
    }

    function init_custom_sidebar(items) {
        add_custom_sidebar(items);
        $('#custom-sidebar').off('click.active').on('click.active', '.sidebar-link', function () {
            $('#custom-sidebar .sidebar-link').removeClass('active');
            $(this).addClass('active');
            const menu = $(this).closest('.sidebar-menu');
            menu.show();
            menu.prev('.sidebar-section').removeClass('collapsed');
            if (window.innerWidth <= 768) {
                $('#custom-sidebar').removeClass('active');
            }
        });
        set_active_link();
    }

    $(document).on('page-change', function () {
        set_active_link();
    }); 

    $(window).on('popstate hashchange', function () {
        set_active_link();
        if (window.handleSidebar) {
            window.handleSidebar();
        }
    });
});
