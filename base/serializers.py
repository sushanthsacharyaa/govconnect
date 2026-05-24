# base/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.validators import ValidationError
from django.utils import timezone
from .models import *
from django.db import transaction


# =========================================================
# CUSTOM USER SERIALIZERS
# =========================================================

class CustomUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'phone_number', 'profile_image',
            'organization_name', 'city', 'state', 'country', 'is_verified',
            'date_joined', 'created_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'is_verified']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password2', 'first_name', 
            'last_name', 'phone_number', 'role', 'organization_name',
            'aadhaar_number', 'pan_number', 'gst_number'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_number', 'profile_image',
            'organization_name', 'address', 'city', 'state', 'postal_code'
        ]
    
    def validate_phone_number(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        if value and len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value


class UserDetailSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = '__all__'
        read_only_fields = ['id', 'username', 'password', 'last_login', 'date_joined', 'created_at']


# =========================================================
# DEPARTMENT SERIALIZERS
# =========================================================

class DepartmentSerializer(serializers.ModelSerializer):
    tender_count = serializers.IntegerField(source='tenders.count', read_only=True)
    
    class Meta:
        model = Department
        fields = ['id', 'department_name', 'description', 'created_at', 'tender_count']
        read_only_fields = ['id', 'created_at']


# =========================================================
# LAND CATEGORY SERIALIZERS
# =========================================================

class LandCategorySerializer(serializers.ModelSerializer):
    land_count = serializers.IntegerField(source='lands.count', read_only=True)
    
    class Meta:
        model = LandCategory
        fields = ['id', 'category_name', 'description', 'land_count']
        read_only_fields = ['id']


# =========================================================
# LAND RECORD SERIALIZERS
# =========================================================

class LandRecordSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.category_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = LandRecord
        fields = [
            'id', 'category', 'category_name', 'survey_number', 'land_title',
            'slug', 'total_area', 'area_unit', 'location', 'district', 'state',
            'latitude', 'longitude', 'market_value', 'ownership_details',
            'land_description', 'land_image', 'status', 'status_display',
            'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']


class LandRecordDetailSerializer(serializers.ModelSerializer):
    category = LandCategorySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    auctions = serializers.SerializerMethodField()
    
    class Meta:
        model = LandRecord
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_auctions(self, obj):
        from .serializers import AuctionListSerializer
        return AuctionListSerializer(obj.auctions.all(), many=True, context=self.context).data


# =========================================================
# TENDER SERIALIZERS
# =========================================================

class TenderSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    published_by_name = serializers.CharField(source='published_by.username', read_only=True)
    status_display = serializers.CharField(source='get_tender_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Tender
        fields = [
            'id', 'tender_id', 'department', 'department_name', 'title', 'slug',
            'description', 'project_budget', 'earnest_money_deposit',
            'eligibility_criteria', 'tender_document', 'start_date', 'end_date',
            'tender_status', 'status_display', 'is_active', 'created_at',
            'published_by', 'published_by_name'
        ]
        read_only_fields = ['id', 'tender_id', 'slug', 'created_at', 'is_active']
    
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise serializers.ValidationError("End date must be after start date")
            
            if start_date < timezone.now():
                raise serializers.ValidationError("Start date cannot be in the past")
        
        return data


class TenderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tender
        fields = [
            'id', 'tender_id', 'title', 'project_budget', 'start_date',
            'end_date', 'tender_status', 'created_at'
        ]


# =========================================================
# AUCTION SERIALIZERS
# =========================================================

class AuctionSerializer(serializers.ModelSerializer):
    land_title = serializers.CharField(source='land.land_title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_auction_status_display', read_only=True)
    is_live = serializers.BooleanField(read_only=True)
    current_highest_bid = serializers.SerializerMethodField()
    total_bids_count = serializers.IntegerField(source='bids.count', read_only=True)
    
    class Meta:
        model = Auction
        fields = [
            'id', 'land', 'land_title', 'auction_title', 'slug', 'reserve_price',
            'minimum_increment_amount', 'auction_start_time', 'auction_end_time',
            'auction_description', 'auction_status', 'status_display', 'is_live',
            'current_highest_bid', 'total_bids_count', 'created_at', 'created_by',
            'created_by_name', 'winner'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'is_live']
    
    def get_current_highest_bid(self, obj):
        if obj.current_highest_bid:
            return obj.current_highest_bid
        return obj.reserve_price


class AuctionListSerializer(serializers.ModelSerializer):
    land_title = serializers.CharField(source='land.land_title', read_only=True)
    current_highest_bid = serializers.SerializerMethodField()
    
    class Meta:
        model = Auction
        fields = [
            'id', 'auction_title', 'land_title', 'reserve_price',
            'auction_start_time', 'auction_end_time', 'auction_status',
            'current_highest_bid'
        ]
    
    def get_current_highest_bid(self, obj):
        if obj.current_highest_bid:
            return obj.current_highest_bid
        return obj.reserve_price


# =========================================================
# BID SERIALIZERS
# =========================================================

class BidSerializer(serializers.ModelSerializer):
    bidder_name = serializers.CharField(source='bidder.username', read_only=True)
    auction_title = serializers.CharField(source='auction.auction_title', read_only=True)
    status_display = serializers.CharField(source='get_bid_status_display', read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            'id', 'auction', 'auction_title', 'bidder', 'bidder_name',
            'bid_amount', 'bid_status', 'status_display', 'submitted_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'bid_status']


class PlaceBidSerializer(serializers.ModelSerializer):
    """
    Serializer for placing a new bid
    Validates the bid amount against auction rules and creates the bid
    """
    class Meta:
        model = Bid
        fields = ['bid_amount']

    def validate(self, attrs):
        auction = self.context.get('auction')
        bidder = self.context.get('bidder')
        bid_amount = attrs.get('bid_amount')

        if not auction:
            raise serializers.ValidationError("Auction not specified")

        # Check if auction is live
        if not auction.is_live():
            raise serializers.ValidationError("Auction is not active")

        # Check if bidder is trying to bid on their own auction
        if auction.created_by == bidder:
            raise serializers.ValidationError("You cannot bid on your own auction")

        # Get current highest bid
        current_highest = auction.current_highest_bid or auction.reserve_price
        
        # Calculate minimum allowed bid
        min_allowed = current_highest + auction.minimum_increment_amount

        # Validate bid amount
        if bid_amount < auction.reserve_price:
            raise serializers.ValidationError(
                f"Bid must be at least the reserve price of ₹{auction.reserve_price:,.2f}"
            )
        
        if bid_amount <= current_highest:
            raise serializers.ValidationError(
                f"Bid must be higher than the current highest bid of ₹{current_highest:,.2f}"
            )
        
        if bid_amount < min_allowed:
            raise serializers.ValidationError(
                f"Minimum bid allowed is ₹{min_allowed:,.2f} "
                f"(Current highest: ₹{current_highest:,.2f} + Minimum increment: ₹{auction.minimum_increment_amount:,.2f})"
            )

        return attrs

    def create(self, validated_data):
        auction = self.context.get('auction')
        bidder = self.context.get('bidder')
        bid_amount = validated_data['bid_amount']

        with transaction.atomic():
            # Mark all existing winning bids as LOST
            auction.bids.filter(bid_status='WINNING').update(bid_status='LOST')
            
            # Create the new winning bid
            bid = Bid.objects.create(
                auction=auction,
                bidder=bidder,
                bid_amount=bid_amount,
                bid_status='WINNING'
            )
            
            # Update auction's current highest bid
            auction.current_highest_bid = bid_amount
            auction.save(update_fields=['current_highest_bid'])

        return bid


# =========================================================
# DOCUMENT VERIFICATION SERIALIZERS
# =========================================================

class DocumentVerificationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    
    class Meta:
        model = DocumentVerification
        fields = [
            'id', 'user', 'user_name', 'document_name', 'document_file',
            'uploaded_at', 'verification_status', 'status_display',
            'verified_by', 'verified_by_name', 'remarks', 'verified_at'
        ]
        read_only_fields = ['id', 'uploaded_at', 'verified_at']


class DocumentVerifySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVerification
        fields = ['verification_status', 'remarks']


# =========================================================
# CONTRACT SERIALIZERS
# =========================================================

class ContractSerializer(serializers.ModelSerializer):
    tender_title = serializers.CharField(source='tender.title', read_only=True)
    contractor_name = serializers.CharField(source='contractor.username', read_only=True)
    status_display = serializers.CharField(source='get_contract_status_display', read_only=True)
    
    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number', 'tender', 'tender_title', 'contractor',
            'contractor_name', 'contract_title', 'contract_document',
            'start_date', 'end_date', 'contract_value', 'contract_status',
            'status_display', 'created_at'
        ]
        read_only_fields = ['id', 'contract_number', 'created_at']


# =========================================================
# PAYMENT SERIALIZERS
# =========================================================

class PaymentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'user', 'user_name', 'amount',
            'payment_type', 'payment_type_display', 'payment_status',
            'status_display', 'payment_date', 'reference_id', 'remarks'
        ]
        read_only_fields = ['id', 'transaction_id', 'payment_date']


class CreatePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_type', 'reference_id', 'remarks']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value


# =========================================================
# NOTIFICATION SERIALIZERS
# =========================================================

class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'type_display',
            'is_read', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


# =========================================================
# GRIEVANCE SERIALIZERS
# =========================================================

class GrievanceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Grievance
        fields = [
            'id', 'user', 'user_name', 'subject', 'description', 'attachment',
            'status', 'status_display', 'created_at', 'resolved_at',
            'resolution_remarks'
        ]
        read_only_fields = ['id', 'created_at', 'resolved_at', 'status']


class GrievanceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grievance
        fields = ['subject', 'description', 'attachment']


class GrievanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grievance
        fields = ['status', 'resolution_remarks']


# =========================================================
# DASHBOARD STATISTICS SERIALIZERS
# =========================================================

class DashboardStatisticsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_lands = serializers.IntegerField()
    total_tenders = serializers.IntegerField()
    total_auctions = serializers.IntegerField()
    total_bids = serializers.IntegerField()
    active_tenders = serializers.IntegerField()
    live_auctions = serializers.IntegerField()
    total_payments = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_grievances = serializers.IntegerField()