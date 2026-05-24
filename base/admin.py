# base/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone_number', 'is_verified', 'created_at')
    list_filter = ('role', 'is_verified', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'profile_image', 'aadhaar_number',
                      'pan_number', 'gst_number', 'organization_name', 'address',
                      'city', 'state', 'country', 'postal_code', 'is_verified')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'aadhaar_number', 'pan_number', 'gst_number')
        }),
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_name', 'created_at')
    search_fields = ('department_name',)
    prepopulated_fields = {}

@admin.register(LandCategory)
class LandCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name',)
    search_fields = ('category_name',)

@admin.register(LandRecord)
class LandRecordAdmin(admin.ModelAdmin):
    list_display = ('land_title', 'survey_number', 'category', 'status', 'market_value', 'district')
    list_filter = ('status', 'category', 'district', 'state')
    search_fields = ('land_title', 'survey_number', 'location')
    prepopulated_fields = {'slug': ('land_title',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'tender_status', 'project_budget', 'start_date', 'end_date')
    list_filter = ('tender_status', 'department')
    search_fields = ('title', 'tender_id')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('auction_title', 'land', 'auction_status', 'reserve_price', 'auction_start_time')
    list_filter = ('auction_status',)
    search_fields = ('auction_title',)
    prepopulated_fields = {'slug': ('auction_title',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'bidder', 'bid_amount', 'bid_status', 'submitted_at')
    list_filter = ('bid_status',)
    search_fields = ('bidder__username', 'auction__auction_title')
    readonly_fields = ('submitted_at',)

@admin.register(DocumentVerification)
class DocumentVerificationAdmin(admin.ModelAdmin):
    list_display = ('document_name', 'user', 'verification_status', 'uploaded_at')
    list_filter = ('verification_status',)
    search_fields = ('document_name', 'user__username')

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_title', 'tender', 'contractor', 'contract_value', 'contract_status')
    list_filter = ('contract_status',)
    search_fields = ('contract_title', 'contract_number')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount', 'payment_type', 'payment_status', 'payment_date')
    list_filter = ('payment_status', 'payment_type')
    search_fields = ('transaction_id', 'user__username')
    readonly_fields = ('payment_date',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at',)

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'status', 'created_at', 'resolved_at')
    list_filter = ('status',)
    search_fields = ('subject', 'user__username')
    readonly_fields = ('created_at',)

# Register models
admin.site.register(CustomUser, CustomUserAdmin)