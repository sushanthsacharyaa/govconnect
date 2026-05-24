# base/management/commands/add_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from base.models import *
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Adds sample data to the database for GovConnect'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Starting to add sample data...'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Track phone numbers to avoid duplicates
        phone_counter = 9900000000
        
        def get_unique_phone():
            nonlocal phone_counter
            phone_counter += 1
            return str(phone_counter)
        
        # =========================================================
        # 1. CREATE DEPARTMENTS
        # =========================================================
        self.stdout.write('\n📁 Creating Departments...')
        departments = [
            {'department_name': 'Ministry of Urban Development', 'description': 'Handles urban development projects and city planning'},
            {'department_name': 'Ministry of Rural Development', 'description': 'Handles rural development and infrastructure projects'},
            {'department_name': 'Public Works Department', 'description': 'Handles public infrastructure and construction projects'},
            {'department_name': 'Water Resources Department', 'description': 'Handles water management and irrigation projects'},
            {'department_name': 'Transport Department', 'description': 'Handles transportation and logistics projects'},
            {'department_name': 'Health Department', 'description': 'Handles healthcare infrastructure projects'},
            {'department_name': 'Education Department', 'description': 'Handles educational infrastructure projects'},
            {'department_name': 'Energy Department', 'description': 'Handles power and energy projects'},
        ]
        
        created_depts = 0
        for dept_data in departments:
            dept, created = Department.objects.get_or_create(
                department_name=dept_data['department_name'],
                defaults={'description': dept_data['description']}
            )
            if created:
                created_depts += 1
                self.stdout.write(f'  ✓ Created department: {dept.department_name}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {created_depts} new departments'))
        
        # =========================================================
        # 2. CREATE LAND CATEGORIES
        # =========================================================
        self.stdout.write('\n🏷 Creating Land Categories...')
        categories = [
            {'category_name': 'Agricultural Land', 'description': 'Land suitable for farming and agricultural activities'},
            {'category_name': 'Residential Land', 'description': 'Land for housing and residential development'},
            {'category_name': 'Commercial Land', 'description': 'Land for business, shopping malls, and commercial complexes'},
            {'category_name': 'Industrial Land', 'description': 'Land for factories, manufacturing units, and industrial zones'},
            {'category_name': 'Government Land', 'description': 'Government-owned land for public use'},
            {'category_name': 'Mixed Use Land', 'description': 'Land suitable for both residential and commercial use'},
            {'category_name': 'Institutional Land', 'description': 'Land for schools, hospitals, and institutions'},
            {'category_name': 'Recreational Land', 'description': 'Land for parks, gardens, and recreational facilities'},
        ]
        
        created_cats = 0
        for cat_data in categories:
            cat, created = LandCategory.objects.get_or_create(
                category_name=cat_data['category_name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                created_cats += 1
                self.stdout.write(f'  ✓ Created category: {cat.category_name}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {created_cats} new categories'))
        
        # =========================================================
        # 3. CREATE USERS
        # =========================================================
        self.stdout.write('\n👥 Creating Users...')
        
        # Create Super Admin
        admin_created = False
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@govconnect.com',
                password='admin123',
                phone_number=get_unique_phone(),
                first_name='Super',
                last_name='Admin',
                role='SUPER_ADMIN',
                is_verified=True
            )
            admin_created = True
            self.stdout.write('  ✓ Created Super Admin: admin / admin123')
        else:
            self.stdout.write('  ⚠ Super Admin already exists')
        
        # Create Government Officers
        officers_data = [
            {'username': 'officer_rajesh', 'email': 'rajesh.kumar@govconnect.com', 'first_name': 'Rajesh', 'last_name': 'Kumar'},
            {'username': 'officer_priya', 'email': 'priya.sharma@govconnect.com', 'first_name': 'Priya', 'last_name': 'Sharma'},
            {'username': 'officer_amit', 'email': 'amit.patel@govconnect.com', 'first_name': 'Amit', 'last_name': 'Patel'},
            {'username': 'officer_sunita', 'email': 'sunita.verma@govconnect.com', 'first_name': 'Sunita', 'last_name': 'Verma'},
            {'username': 'officer_vikram', 'email': 'vikram.singh@govconnect.com', 'first_name': 'Vikram', 'last_name': 'Singh'},
        ]
        
        created_officers = 0
        for officer_data in officers_data:
            if not User.objects.filter(username=officer_data['username']).exists():
                try:
                    officer = User.objects.create_user(
                        username=officer_data['username'],
                        email=officer_data['email'],
                        password='officer123',
                        phone_number=get_unique_phone(),
                        first_name=officer_data['first_name'],
                        last_name=officer_data['last_name'],
                        role='GOVERNMENT_OFFICER',
                        is_verified=True
                    )
                    created_officers += 1
                    self.stdout.write(f'  ✓ Created Government Officer: {officer_data["username"]} / officer123')
                except Exception as e:
                    self.stdout.write(f'  ✗ Failed to create {officer_data["username"]}: {str(e)}')
            else:
                self.stdout.write(f'  ⚠ Officer already exists: {officer_data["username"]}')
        
        # Create Tender Publishers
        publishers_data = [
            {'username': 'publisher_urban', 'email': 'urban.dept@govconnect.com', 'first_name': 'Urban', 'last_name': 'Dept', 'dept': 'Ministry of Urban Development'},
            {'username': 'publisher_rural', 'email': 'rural.dept@govconnect.com', 'first_name': 'Rural', 'last_name': 'Dept', 'dept': 'Ministry of Rural Development'},
            {'username': 'publisher_pwd', 'email': 'pwd@govconnect.com', 'first_name': 'PWD', 'last_name': 'Dept', 'dept': 'Public Works Department'},
        ]
        
        created_publishers = 0
        for pub_data in publishers_data:
            if not User.objects.filter(username=pub_data['username']).exists():
                try:
                    publisher = User.objects.create_user(
                        username=pub_data['username'],
                        email=pub_data['email'],
                        password='publisher123',
                        phone_number=get_unique_phone(),
                        first_name=pub_data['first_name'],
                        last_name=pub_data['last_name'],
                        organization_name=pub_data['dept'],
                        role='TENDER_PUBLISHER',
                        is_verified=True
                    )
                    created_publishers += 1
                    self.stdout.write(f'  ✓ Created Tender Publisher: {pub_data["username"]} / publisher123')
                except Exception as e:
                    self.stdout.write(f'  ✗ Failed to create {pub_data["username"]}: {str(e)}')
            else:
                self.stdout.write(f'  ⚠ Publisher already exists: {pub_data["username"]}')
        
        # Create Bidders/Contractors with unique phone numbers
        bidders_data = [
            {'username': 'bidder_mohan', 'email': 'mohan.singh@constructions.com', 'first_name': 'Mohan', 'last_name': 'Singh', 'org': 'Singh Constructions', 'role': 'BIDDER'},
            {'username': 'bidder_sita', 'email': 'sita.reddy@builders.com', 'first_name': 'Sita', 'last_name': 'Reddy', 'org': 'Reddy Builders', 'role': 'BIDDER'},
            {'username': 'bidder_ahmed', 'email': 'ahmed.khan@developers.com', 'first_name': 'Ahmed', 'last_name': 'Khan', 'org': 'Khan Developers', 'role': 'BIDDER'},
            {'username': 'contractor_vikram', 'email': 'vikram@malhotragroup.com', 'first_name': 'Vikram', 'last_name': 'Malhotra', 'org': 'Malhotra Group', 'role': 'CONTRACTOR'},
            {'username': 'contractor_neha', 'email': 'neha@guptainfra.com', 'first_name': 'Neha', 'last_name': 'Gupta', 'org': 'Gupta Infra', 'role': 'CONTRACTOR'},
            {'username': 'bidder_ravi', 'email': 'ravi.kumar@enterprises.com', 'first_name': 'Ravi', 'last_name': 'Kumar', 'org': 'Ravi Enterprises', 'role': 'BIDDER'},
            {'username': 'bidder_poonam', 'email': 'poonam.jain@group.com', 'first_name': 'Poonam', 'last_name': 'Jain', 'org': 'Jain Group', 'role': 'BIDDER'},
        ]
        
        created_bidders = 0
        for bidder_data in bidders_data:
            if not User.objects.filter(username=bidder_data['username']).exists():
                try:
                    bidder = User.objects.create_user(
                        username=bidder_data['username'],
                        email=bidder_data['email'],
                        password='bidder123',
                        phone_number=get_unique_phone(),
                        first_name=bidder_data['first_name'],
                        last_name=bidder_data['last_name'],
                        organization_name=bidder_data['org'],
                        role=bidder_data['role'],
                        is_verified=True
                    )
                    created_bidders += 1
                    self.stdout.write(f'  ✓ Created {bidder_data["role"]}: {bidder_data["username"]} / bidder123')
                except Exception as e:
                    self.stdout.write(f'  ✗ Failed to create {bidder_data["username"]}: {str(e)}')
            else:
                self.stdout.write(f'  ⚠ User already exists: {bidder_data["username"]}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {created_officers} officers, {created_publishers} publishers, {created_bidders} bidders/contractors'))
        
        # =========================================================
        # 4. CREATE LAND RECORDS
        # =========================================================
        self.stdout.write('\n🏞 Creating Land Records...')
        
        # Get categories for reference
        categories_dict = {}
        for cat in LandCategory.objects.all():
            categories_dict[cat.category_name] = cat
        
        lands_data = [
            {
                'title': 'Greenfield Agricultural Estate',
                'survey_no': 'SURV001',
                'category': 'Agricultural Land',
                'area': 45.5,
                'location': 'Greenfield Village',
                'district': 'North Delhi',
                'state': 'Delhi',
                'value': 7500000,
                'description': 'Prime agricultural land with modern irrigation facilities and fertile soil.',
                'ownership': 'Government of Delhi',
                'status': 'AVAILABLE'
            },
            {
                'title': 'City Center Commercial Hub',
                'survey_no': 'SURV002',
                'category': 'Commercial Land',
                'area': 8.0,
                'location': 'Connaught Place',
                'district': 'Central Delhi',
                'state': 'Delhi',
                'value': 35000000,
                'description': 'Premium commercial property in the heart of the city.',
                'ownership': 'Delhi Development Authority',
                'status': 'AVAILABLE'
            },
            {
                'title': 'Industrial Zone Plot A',
                'survey_no': 'SURV003',
                'category': 'Industrial Land',
                'area': 25.0,
                'location': 'Noida Special Economic Zone',
                'district': 'Gautam Buddha Nagar',
                'state': 'Uttar Pradesh',
                'value': 18000000,
                'description': 'Ready-to-build industrial plot with all utilities.',
                'ownership': 'UP State Industrial Corporation',
                'status': 'UNDER_AUCTION'
            },
            {
                'title': 'Luxury Residential Township',
                'survey_no': 'SURV004',
                'category': 'Residential Land',
                'area': 75.0,
                'location': 'Gurugram Sector 62',
                'district': 'Gurugram',
                'state': 'Haryana',
                'value': 55000000,
                'description': 'Large residential development area approved for luxury housing project.',
                'ownership': 'Haryana Urban Development Authority',
                'status': 'AVAILABLE'
            },
            {
                'title': 'Waterfront Commercial Property',
                'survey_no': 'SURV005',
                'category': 'Commercial Land',
                'area': 12.5,
                'location': 'Marine Drive',
                'district': 'Mumbai',
                'state': 'Maharashtra',
                'value': 65000000,
                'description': 'Premium waterfront commercial property with sea view.',
                'ownership': 'Mumbai Municipal Corporation',
                'status': 'AVAILABLE'
            },
        ]
        
        created_lands = 0
        for land_data in lands_data:
            if not LandRecord.objects.filter(survey_number=land_data['survey_no']).exists():
                category = categories_dict.get(land_data['category'])
                if category:
                    land = LandRecord.objects.create(
                        category=category,
                        survey_number=land_data['survey_no'],
                        land_title=land_data['title'],
                        total_area=land_data['area'],
                        area_unit='Acres',
                        location=land_data['location'],
                        district=land_data['district'],
                        state=land_data['state'],
                        market_value=land_data['value'],
                        ownership_details=land_data['ownership'],
                        land_description=land_data['description'],
                        status=land_data['status']
                    )
                    created_lands += 1
                    self.stdout.write(f'  ✓ Created land: {land.land_title}')
                else:
                    self.stdout.write(f'  ✗ Category not found for: {land_data["title"]}')
            else:
                self.stdout.write(f'  ⚠ Land already exists: {land_data["title"]}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {created_lands} new land records'))
        
        # =========================================================
        # 5. CREATE TENDERS
        # =========================================================
        self.stdout.write('\n📋 Creating Tenders...')
        
        # Get departments and publishers
        dept_dict = {}
        for dept in Department.objects.all():
            dept_dict[dept.department_name] = dept
        
        publisher_dict = {}
        for pub in User.objects.filter(role='TENDER_PUBLISHER'):
            publisher_dict[pub.username] = pub
        
        # Use default publisher if specific one doesn't exist
        default_publisher = User.objects.filter(role__in=['GOVERNMENT_OFFICER', 'SUPER_ADMIN']).first()
        
        tenders_data = [
            {
                'title': 'Construction of Elevated Corridor',
                'dept': 'Ministry of Urban Development',
                'budget': 85000000,
                'emd': 850000,
                'description': 'Construction of 6-lane elevated corridor with modern lighting and drainage system.',
                'eligibility': 'Class A contractor with minimum 15 years of experience.',
                'days': 45
            },
            {
                'title': 'Rural Road Connectivity Program',
                'dept': 'Ministry of Rural Development',
                'budget': 35000000,
                'emd': 350000,
                'description': 'Construction of rural roads connecting 100 villages under PMGSY scheme.',
                'eligibility': 'Registered contractor with PWD and experience in rural road construction.',
                'days': 60
            },
            {
                'title': 'Smart City Infrastructure Project',
                'dept': 'Ministry of Urban Development',
                'budget': 120000000,
                'emd': 1200000,
                'description': 'Development of smart city infrastructure including IoT sensors and smart lighting.',
                'eligibility': 'Companies with proven experience in smart city projects.',
                'days': 90
            },
            {
                'title': 'Water Treatment Plant',
                'dept': 'Water Resources Department',
                'budget': 45000000,
                'emd': 450000,
                'description': 'Construction of 50 MLD water treatment plant with modern filtration technology.',
                'eligibility': 'Experience in water treatment infrastructure projects.',
                'days': 120
            },
            {
                'title': 'District Hospital Upgrade',
                'dept': 'Health Department',
                'budget': 65000000,
                'emd': 650000,
                'description': 'Upgradation of district hospital with modern equipment and additional floors.',
                'eligibility': 'Experience in healthcare infrastructure projects.',
                'days': 150
            },
        ]
        
        created_tenders = 0
        for tender_data in tenders_data:
            if not Tender.objects.filter(title=tender_data['title']).exists():
                department = dept_dict.get(tender_data['dept'])
                publisher = default_publisher
                
                if department and publisher:
                    tender = Tender.objects.create(
                        department=department,
                        published_by=publisher,
                        title=tender_data['title'],
                        description=tender_data['description'],
                        project_budget=tender_data['budget'],
                        earnest_money_deposit=tender_data['emd'],
                        eligibility_criteria=tender_data['eligibility'],
                        start_date=timezone.now(),
                        end_date=timezone.now() + timedelta(days=tender_data['days']),
                        tender_status='OPEN'
                    )
                    created_tenders += 1
                    self.stdout.write(f'  ✓ Created tender: {tender.title}')
                else:
                    self.stdout.write(f'  ✗ Missing department or publisher for: {tender_data["title"]}')
            else:
                self.stdout.write(f'  ⚠ Tender already exists: {tender_data["title"]}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {created_tenders} new tenders'))
        
        # =========================================================
        # 6. CREATE AUCTIONS
        # =========================================================
        self.stdout.write('\n🔨 Creating Auctions...')
        
        lands_for_auction = LandRecord.objects.filter(status='AVAILABLE')[:3]
        auctioneer = User.objects.filter(role='GOVERNMENT_OFFICER').first()
        
        auctions_data = [
            {
                'title': 'Premium Commercial Land Auction',
                'reserve': 35000000,
                'increment': 500000,
                'description': 'Auction for prime commercial land in city center.',
                'start_days': 0,
                'end_days': 15
            },
            {
                'title': 'Industrial Plot Auction',
                'reserve': 18000000,
                'increment': 250000,
                'description': 'Auction for industrial plot in SEZ with all utilities.',
                'start_days': 2,
                'end_days': 20
            },
            {
                'title': 'Residential Land Auction',
                'reserve': 55000000,
                'increment': 750000,
                'description': 'Large residential development land.',
                'start_days': 5,
                'end_days': 25
            },
        ]
        
        created_auctions = 0
        for i, auction_data in enumerate(auctions_data):
            if i < len(lands_for_auction) and lands_for_auction[i]:
                if not Auction.objects.filter(auction_title=auction_data['title']).exists():
                    start_time = timezone.now() + timedelta(days=auction_data['start_days'])
                    auction = Auction.objects.create(
                        land=lands_for_auction[i],
                        created_by=auctioneer,
                        auction_title=auction_data['title'],
                        reserve_price=auction_data['reserve'],
                        minimum_increment_amount=auction_data['increment'],
                        auction_start_time=start_time,
                        auction_end_time=timezone.now() + timedelta(days=auction_data['end_days']),
                        auction_description=auction_data['description'],
                        auction_status='LIVE' if auction_data['start_days'] == 0 else 'UPCOMING'
                    )
                    created_auctions += 1
                    self.stdout.write(f'  ✓ Created auction: {auction.auction_title}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {created_auctions} new auctions'))
        
        # =========================================================
        # 7. CREATE BIDS
        # =========================================================
        self.stdout.write('\n💰 Creating Sample Bids...')
        
        live_auctions = Auction.objects.filter(auction_status='LIVE')
        bidders = User.objects.filter(role='BIDDER')[:3]
        
        created_bids = 0
        for auction in live_auctions:
            for i, bidder in enumerate(bidders):
                if not Bid.objects.filter(auction=auction, bidder=bidder).exists():
                    bid_amount = auction.reserve_price + ((i + 1) * auction.minimum_increment_amount)
                    bid_status = 'WINNING' if i == 0 else 'LOST'
                    
                    Bid.objects.create(
                        auction=auction,
                        bidder=bidder,
                        bid_amount=bid_amount,
                        bid_status=bid_status
                    )
                    created_bids += 1
                    self.stdout.write(f'  ✓ Created bid: {bidder.username} - ₹{bid_amount:,.2f}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {created_bids} new bids'))
        
        # =========================================================
        # FINAL SUMMARY
        # =========================================================
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('📊 FINAL SUMMARY'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  👥 Users: {CustomUser.objects.count()}')
        self.stdout.write(f'  🏢 Departments: {Department.objects.count()}')
        self.stdout.write(f'  🏷 Categories: {LandCategory.objects.count()}')
        self.stdout.write(f'  🏞 Land Records: {LandRecord.objects.count()}')
        self.stdout.write(f'  📋 Tenders: {Tender.objects.count()}')
        self.stdout.write(f'  🔨 Auctions: {Auction.objects.count()}')
        self.stdout.write(f'  💰 Bids: {Bid.objects.count()}')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('\n🎉 Sample data added successfully!'))
        self.stdout.write(self.style.SUCCESS('\n📝 Login Credentials:'))
        self.stdout.write('  Super Admin: admin / admin123')
        
        # Show existing officer credentials
        officer = User.objects.filter(role='GOVERNMENT_OFFICER').first()
        if officer:
            self.stdout.write(f'  Government Officer: {officer.username} / officer123')
        
        # Show existing bidder credentials
        bidder = User.objects.filter(role='BIDDER').first()
        if bidder:
            self.stdout.write(f'  Bidder: {bidder.username} / bidder123')
        
        self.stdout.write('=' * 60)