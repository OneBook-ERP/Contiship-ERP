frappe.pages['consignment-report'].on_page_load = function (wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Consignment Report',
        single_column: true
    });

    const $fieldset = "";

    page.add_field({
        label: 'Select Report Type',
        fieldname: 'report_type',
        fieldtype: 'Select',
        options: ['Live Stock Report', 'Closing Stock Report', 'Sales Bill Report'].join('\n'),
        default: 'Live Stock Report',
        reqd: 1,
        parent: $fieldset,
        columns: 12
    });

    page.add_field({
        label: 'Customer',
        fieldname: 'customer',
        fieldtype: 'Link',
        options: 'Customer',
        reqd: 1,
        parent: $fieldset,
        columns: 12
    });

    page.add_field({
        label: 'Consignment No / Container ID',
        fieldname: 'consignment_no',
        fieldtype: 'Data',
        parent: $fieldset,
        columns: 12
    });

    page.add_field({
        label: 'From Date',
        fieldname: 'from_date',
        fieldtype: 'Date',
        default: frappe.datetime.now_date(),
        reqd: 1,
        parent: $fieldset,
        columns: 6
    });

    page.add_field({
        label: 'To Date',
        fieldname: 'to_date',
        fieldtype: 'Date',
        default: frappe.datetime.now_date(),
        reqd: 1,
        parent: $fieldset,
        columns: 6
    });

    page.report_container = page.body
        .append('<div class="consignment-report-results mt-4"></div>')
        .find('.consignment-report-results');

    page.datatable = null;

    page.add_inner_button('Generate Report', function () {
        const filters = {
            report_type: page.fields_dict.report_type.get_value(),
            from_date: page.fields_dict.from_date.get_value(),
            to_date: page.fields_dict.to_date.get_value(),
            customer: page.fields_dict.customer.get_value(),
            consignment_no: page.fields_dict.consignment_no.get_value()
        };

        if (!filters.report_type || !filters.from_date || !filters.to_date || !filters.customer) {
            frappe.throw('Please fill all mandatory fields (Report Type, Dates, Customer).');
            return;
        }

        page.report_container.empty().append(`
            <div class="text-center text-muted p-5">
                <i class="fa fa-spinner fa-spin fa-2x"></i>
                <p class="mt-2">Fetching report data...</p>
            </div>
        `);

        frappe.call({
            method: 'contiship_erp.contiship_erp.page.consignment_report.consignment_report.get_consignment_report_data',
            args: { filters: JSON.stringify(filters) },

            callback: function (r) {
                page.report_container.empty();

                if (r.message && r.message.data && r.message.columns) {
                    const { data, columns } = r.message;

                    // --- Convert column labels ---
                    const enhancedColumns = columns.map(col => ({
                        id: col.fieldname,
                        content: col.label || col.fieldname,
                        align: 'left'
                    }));

                    // --- Tree structure support ---
                    // Each item in data must have `is_group` and optional `children`
                    const makeTreeData = (rows) => {
                        return rows.map(row => ({
                            ...row,
                            is_tree: row.is_group ? 1 : 0,
                            children: row.children ? makeTreeData(row.children) : []
                        }));
                    };

                    const treeData = makeTreeData(data);

                    // --- Destroy old table ---
                    if (page.datatable) page.datatable.destroy();

                    // --- Create Tree DataTable ---
                    page.datatable = new frappe.DataTable(page.report_container[0], {
                        columns: enhancedColumns,
                        data: treeData,
                        getChildren: (row) => row.children || [],
                        isTree: true,
                        showTotalRow: true,
                        enableClusterize: true,
                        cellHeight: 30,
                        noDataMessage: "No records found",
                        checkboxColumn: false
                    });

                } else {
                    page.report_container.html(`
                        <p class="text-muted text-center p-5">
                            No data found or unexpected response.
                        </p>
                    `);
                }
            }
        });
    }).addClass('btn-primary');
};
