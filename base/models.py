# base/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('SUPER_ADMIN', 'Super Admin'),
        ('GOVERNMENT_OFFICER', 'Government Officer'),
        ('TENDER_PUBLISHER', 'Tender Publisher'),
        ('BIDDER', 'Bidder'),
        ('CONTRACTOR', 'Contractor'),
        ('AUCTIONEER', 'Auctioneer'),
        ('LEGAL_OFFICER', 'Legal Officer'),
        ('LAND_INSPECTOR', 'Land Inspector'),
        ('FINANCE_OFFICER', 'Finance Officer'),
        ('PUBLIC_VIEWER', 'Public Viewer'),
    )

    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='PUBLIC_VIEWER')
    phone_number = models.CharField(max_length=15, unique=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    aadhaar_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    gst_number = models.CharField(max_length=30, blank=True, null=True, unique=True)
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['role']), models.Index(fields=['is_verified']), models.Index(fields=['-created_at'])]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Department(models.Model):
    department_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Departments'

    def __str__(self):
        return self.department_name


class LandCategory(models.Model):
    category_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Land Categories'

    def __str__(self):
        return self.category_name


class LandRecord(models.Model):
    LAND_STATUS = (
        ('AVAILABLE', 'Available'),
        ('UNDER_AUCTION', 'Under Auction'),
        ('SOLD', 'Sold'),
        ('LEASED', 'Leased'),
    )

    category = models.ForeignKey(LandCategory, on_delete=models.CASCADE, related_name='lands')
    survey_number = models.CharField(max_length=100, unique=True)
    land_title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    total_area = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    area_unit = models.CharField(max_length=50, default='Acres')
    location = models.CharField(max_length=255)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    market_value = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    ownership_details = models.TextField()
    zoning_information = models.TextField(blank=True, null=True)
    land_description = models.TextField()
    land_image = models.ImageField(upload_to='land_images/', blank=True, null=True)
    status = models.CharField(max_length=30, choices=LAND_STATUS, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.land_title}-{uuid.uuid4().hex[:5]}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.land_title


class Tender(models.Model):
    TENDER_STATUS = (
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
        ('AWARDED', 'Awarded'),
    )

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='tenders')
    published_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='published_tenders')
    tender_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    project_budget = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    earnest_money_deposit = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    eligibility_criteria = models.TextField()
    tender_document = models.FileField(upload_to='tender_documents/')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    tender_status = models.CharField(max_length=20, choices=TENDER_STATUS, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{uuid.uuid4().hex[:5]}")
        super().save(*args, **kwargs)

    def is_active(self):
        return self.end_date > timezone.now() and self.tender_status == 'OPEN'

    def __str__(self):
        return self.title


class Auction(models.Model):
    AUCTION_STATUS = (
        ('UPCOMING', 'Upcoming'),
        ('LIVE', 'Live'),
        ('ENDED', 'Ended'),
        ('CANCELLED', 'Cancelled'),
    )

    land = models.ForeignKey(LandRecord, on_delete=models.CASCADE, related_name='auctions')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_auctions')
    auction_title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    reserve_price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    minimum_increment_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    auction_start_time = models.DateTimeField()
    auction_end_time = models.DateTimeField()
    auction_description = models.TextField()
    auction_status = models.CharField(max_length=20, choices=AUCTION_STATUS, default='UPCOMING')
    current_highest_bid = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, default=0)
    winner = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_auctions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['auction_status']),
            models.Index(fields=['auction_start_time', 'auction_end_time']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.auction_title}-{uuid.uuid4().hex[:5]}")
        super().save(*args, **kwargs)

    def is_live(self):
        now = timezone.now()
        return self.auction_start_time <= now <= self.auction_end_time and self.auction_status == 'LIVE'

    def __str__(self):
        return self.auction_title


class Bid(models.Model):
    BID_STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('WINNING', 'Winning'),
        ('LOST', 'Lost'),
    )

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bids')
    bid_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    bid_status = models.CharField(max_length=20, choices=BID_STATUS, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-bid_amount']
        unique_together = ['auction', 'bidder']

    def __str__(self):
        return f"{self.bidder.username} - ₹{self.bid_amount}"


class DocumentVerification(models.Model):
    VERIFICATION_STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='documents')
    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to='verification_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='PENDING')
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    remarks = models.TextField(blank=True, null=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.document_name} - {self.user.username}"


class Contract(models.Model):
    CONTRACT_STATUS = (
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('TERMINATED', 'Terminated'),
    )

    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='contracts', null=True, blank=True)
    contractor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='contracts')
    contract_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    contract_title = models.CharField(max_length=255)
    contract_document = models.FileField(upload_to='contracts/')
    start_date = models.DateField()
    end_date = models.DateField()
    contract_value = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    contract_status = models.CharField(max_length=20, choices=CONTRACT_STATUS, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.contract_title


class Payment(models.Model):
    PAYMENT_TYPES = (
        ('EMD', 'EMD'),
        ('TENDER_FEE', 'Tender Fee'),
        ('AUCTION_PAYMENT', 'Auction Payment'),
        ('REFUND', 'Refund'),
    )

    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPES)
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    payment_date = models.DateTimeField(auto_now_add=True)
    reference_id = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.transaction_id)


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('BID', 'Bid'),
        ('AUCTION', 'Auction'),
        ('PAYMENT', 'Payment'),
        ('TENDER', 'Tender'),
        ('GENERAL', 'General'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='GENERAL')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Grievance(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='grievances')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    attachment = models.FileField(upload_to='grievances/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolution_remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.subject