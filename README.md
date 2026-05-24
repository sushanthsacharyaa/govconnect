# GovConnect - Government Land & Tender Management System

## About The Project
GovConnect is a comprehensive e-governance platform that digitizes government land auctions, tender management, and contractor bidding processes.

## Features
- Multi-Role Authentication (10 user roles)
- Real-Time Land Auctions with automatic bid validation
- Tender Management with document support
- Payment Processing with transaction history
- Document Verification workflow
- Real-Time Notifications
- Role-Specific Dashboards
- Grievance Redressal System

## Tech Stack
- **Backend:** Django 5.2, Django REST Framework
- **Frontend:** Bootstrap 5, JavaScript, jQuery
- **Database:** SQLite

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/govconnect.git

# Navigate to project
cd govconnect

# Create virtual environment
python -m venv myenv

# Activate virtual environment (Windows)
myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver

Demo Credentials
Admin: admin / admin123

Bidder: bidder_mohan / bidder123

Author
Your Name
