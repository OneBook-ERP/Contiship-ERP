# ContiShip ERP - Warehouse & Inventory Management

## Overview

ContiShip ERP is a comprehensive Warehouse and Inventory Management System built on the Frappe/ERPNext framework. It provides robust tools for managing warehouse operations, inventory tracking, and logistics management with a focus on efficiency and user experience.

## Features

### Core Modules

- **Inward/Outward Management**
  - Track incoming and outgoing shipments
  - Detailed item-wise entry and validation
  - Barcode/RFID support for quick scanning

- **Container Management**
  - Track container movements and contents
  - Real-time container status updates
  - Detailed container history and audit trail

- **Consignment Tracking**
  - End-to-end consignment lifecycle management
  - Customer-specific consignment handling
  - Automated status updates and notifications

- **Repacking Operations**
  - Manage repacking processes
  - Track item transformations
  - Maintain repacking history and audit logs

- **Customer Traffic Configuration**
  - Customizable customer-specific rules
  - Traffic pattern analysis
  - Automated workflow triggers

## Prerequisites

- Frappe Bench
- Frappe & ERPNext 15+
- Python 3.7+
- Node.js 14+
- MariaDB 10.3+ / PostgreSQL 9.5+
- Redis 5+

## Installation

1. **Set up Frappe Bench** (if not already installed):
   ```bash
   pip install frappe-bench
   bench init frappe-bench
   cd frappe-bench
   ```

2. **Create a new site** (skip if using existing site):
   ```bash
   bench new-site your-site-name
   ```

3. **Install ContiShip ERP**:
   ```bash
   bench get-app contiship_erp https://github.com/your-org/contiship_erp
   bench --site your-site-name install-app contiship_erp
   ```

4. **Start the development server**:
   ```bash
   bench start
   ```

## Configuration

### System Settings
1. Navigate to `Setup > Settings > ContiShip Settings`
2. Configure the following:
   - Default Warehouse
   - Barcode Settings
   - Notification Preferences
   - Integration Settings

### User Permissions
1. Go to `Users and Permissions > Role Permissions Manager`
2. Assign appropriate roles to users:
   - Warehouse Manager
   - Inventory User
   - Auditor
   - System Manager

## Usage

### Creating an Inward Entry
1. Navigate to `Warehouse > Inward Entry > New`
2. Fill in the required details:
   - Supplier Information
   - Delivery Note
   - Item Details
   - Storage Location
3. Save and Submit the entry

### Managing Inventory
1. Access `Stock > Items`
2. View current stock levels
3. Perform stock adjustments if needed
4. Generate stock reports

## Development

### Setup Development Environment
```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Style
The project follows PEP 8 guidelines and uses:
- `ruff` for Python linting
- `eslint` for JavaScript linting
- `prettier` for code formatting
- `pyupgrade` for Python version upgrades

### Running Tests
```bash
# Run Python tests
bench --site your-site-name run-tests --module contiship_erp

# Run JavaScript tests
cd ./contiship_erp && npm test
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For support, please contact:
- Email: jaga@onebook.app
- Issue Tracker: [GitHub Issues](https://github.com/your-org/contiship_erp/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Frappe Framework](https://frappeframework.com/)
- Inspired by modern warehouse management practices
- Special thanks to all contributors

---

*ContiShip ERP - Streamlining Your Warehouse Operations*
