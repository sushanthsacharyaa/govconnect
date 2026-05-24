# base/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    CustomUser, Department, LandCategory, LandRecord, Tender,
    Auction, Bid, DocumentVerification, Contract, Payment,
    Notification, Grievance
)
import re


# =========================================================
# CUSTOM USER FORMS
# =========================================================

class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users with all required fields"""
    
    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'password1', 'password2', 'role',
            'first_name', 'last_name', 'phone_number', 'profile_image',
            'aadhaar_number', 'pan_number', 'gst_number', 'organization_name',
            'address', 'city', 'state', 'country', 'postal_code'
        )
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and not re.match(r'^[0-9]{10,15}$', phone):
            raise ValidationError('Enter a valid phone number (10-15 digits)')
        return phone

    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get('aadhaar_number')
        if aadhaar and not re.match(r'^[0-9]{12}$', aadhaar):
            raise ValidationError('Aadhaar number must be 12 digits')
        return aadhaar

    def clean_pan_number(self):
        pan = self.cleaned_data.get('pan_number')
        if pan and not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan):
            raise ValidationError('Enter a valid PAN number (e.g., ABCDE1234F)')
        return pan


class CustomUserChangeForm(UserChangeForm):
    """Form for updating user information"""
    
    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'role', 'first_name', 'last_name',
            'phone_number', 'profile_image', 'aadhaar_number', 'pan_number',
            'gst_number', 'organization_name', 'address', 'city', 'state',
            'country', 'postal_code', 'is_verified'
        )
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class UserProfileUpdateForm(forms.ModelForm):
    """Form for users to update their own profile"""
    
    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'phone_number', 'profile_image',
            'organization_name', 'address', 'city', 'state', 'postal_code'
        )
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
        }


# =========================================================
# DEPARTMENT FORMS
# =========================================================

class DepartmentForm(forms.ModelForm):
    
    class Meta:
        model = Department
        fields = ['department_name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'department_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


# =========================================================
# LAND CATEGORY FORMS
# =========================================================

class LandCategoryForm(forms.ModelForm):
    
    class Meta:
        model = LandCategory
        fields = ['category_name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


# =========================================================
# LAND RECORD FORMS
# =========================================================

class LandRecordForm(forms.ModelForm):
    
    class Meta:
        model = LandRecord
        fields = [
            'category', 'survey_number', 'land_title', 'total_area',
            'area_unit', 'location', 'district', 'state', 'latitude',
            'longitude', 'market_value', 'ownership_details',
            'zoning_information', 'land_description', 'land_image', 'status'
        ]
        widgets = {
            'ownership_details': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'zoning_information': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'land_description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001', 'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001', 'class': 'form-control'}),
        }

    def clean_survey_number(self):
        survey_no = self.cleaned_data.get('survey_number')
        if LandRecord.objects.filter(survey_number=survey_no).exists():
            if not self.instance.pk or self.instance.survey_number != survey_no:
                raise ValidationError('Survey number already exists')
        return survey_no

    def clean_market_value(self):
        value = self.cleaned_data.get('market_value')
        if value and value < 0:
            raise ValidationError('Market value cannot be negative')
        return value

    def clean_total_area(self):
        area = self.cleaned_data.get('total_area')
        if area and area <= 0:
            raise ValidationError('Total area must be greater than 0')
        return area


class LandSearchForm(forms.Form):
    """Form for searching land records"""
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search by title, location...'}))
    category = forms.ModelChoiceField(queryset=LandCategory.objects.all(), required=False)
    district = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'District'}))
    state = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'State'}))
    min_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'Min Price'}))
    max_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'Max Price'}))
    status = forms.ChoiceField(choices=[('', 'All')] + list(LandRecord.LAND_STATUS), required=False)


# =========================================================
# TENDER FORMS
# =========================================================

class TenderForm(forms.ModelForm):
    
    class Meta:
        model = Tender
        fields = [
            'department', 'title', 'description', 'project_budget',
            'earnest_money_deposit', 'eligibility_criteria', 'tender_document',
            'start_date', 'end_date', 'tender_status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'eligibility_criteria': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'project_budget': forms.NumberInput(attrs={'class': 'form-control'}),
            'earnest_money_deposit': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError('End date must be after start date')
            
            if start_date < timezone.now():
                raise ValidationError('Start date cannot be in the past')
        
        project_budget = cleaned_data.get('project_budget')
        emd = cleaned_data.get('earnest_money_deposit')
        
        if project_budget and emd and emd > project_budget:
            raise ValidationError('EMD cannot exceed project budget')
        
        return cleaned_data


class TenderSearchForm(forms.Form):
    """Form for searching tenders"""
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search by title...'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    status = forms.ChoiceField(choices=[('', 'All')] + list(Tender.TENDER_STATUS), required=False)
    min_budget = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'Min Budget'}))
    max_budget = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'Max Budget'}))
    is_active = forms.BooleanField(required=False, label='Show Active Only')


# =========================================================
# AUCTION FORMS
# =========================================================

class AuctionForm(forms.ModelForm):
    
    class Meta:
        model = Auction
        fields = [
            'land', 'auction_title', 'reserve_price', 'minimum_increment_amount',
            'auction_start_time', 'auction_end_time', 'auction_description'
        ]
        widgets = {
            'auction_description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'auction_start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'auction_end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'reserve_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_increment_amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('auction_start_time')
        end_time = cleaned_data.get('auction_end_time')
        reserve_price = cleaned_data.get('reserve_price')
        min_increment = cleaned_data.get('minimum_increment_amount')
        
        if start_time and end_time:
            if end_time <= start_time:
                raise ValidationError('End time must be after start time')
        
        if reserve_price and reserve_price < 0:
            raise ValidationError('Reserve price cannot be negative')
        
        if min_increment and min_increment <= 0:
            raise ValidationError('Minimum increment must be positive')
        
        return cleaned_data


class BidForm(forms.ModelForm):
    
    class Meta:
        model = Bid
        fields = ['bid_amount']
        widgets = {
            'bid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.auction = kwargs.pop('auction', None)
        self.bidder = kwargs.pop('bidder', None)
        super().__init__(*args, **kwargs)

    def clean_bid_amount(self):
        bid_amount = self.cleaned_data.get('bid_amount')
        
        if not self.auction:
            raise ValidationError('Auction not specified')
        
        # Check if auction is live
        if not self.auction.is_live():
            raise ValidationError('Auction is not active')
        
        # Check minimum bid amount
        if bid_amount < self.auction.reserve_price:
            raise ValidationError(f'Bid must be at least reserve price: {self.auction.reserve_price}')
        
        # Check if higher than current highest bid
        highest_bid = self.auction.bids.filter(bid_status='WINNING').first()
        if highest_bid:
            min_bid = highest_bid.bid_amount + self.auction.minimum_increment_amount
            if bid_amount < min_bid:
                raise ValidationError(f'Bid must be at least {min_bid} (current highest + increment)')
        
        return bid_amount


# =========================================================
# DOCUMENT VERIFICATION FORMS
# =========================================================

class DocumentVerificationForm(forms.ModelForm):
    
    class Meta:
        model = DocumentVerification
        fields = ['document_name', 'document_file']
        widgets = {
            'document_name': forms.TextInput(attrs={'class': 'form-control'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class DocumentVerificationAdminForm(forms.ModelForm):
    """Form for admin to verify documents"""
    
    class Meta:
        model = DocumentVerification
        fields = ['verification_status', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'verification_status': forms.Select(attrs={'class': 'form-control'}),
        }


# =========================================================
# CONTRACT FORMS
# =========================================================

class ContractForm(forms.ModelForm):
    
    class Meta:
        model = Contract
        fields = [
            'tender', 'contractor', 'contract_title', 'contract_document',
            'start_date', 'end_date', 'contract_value', 'contract_status'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'contract_title': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_value': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise ValidationError('End date must be after start date')
        
        return cleaned_data


# =========================================================
# PAYMENT FORMS
# =========================================================

class PaymentForm(forms.ModelForm):
    
    class Meta:
        model = Payment
        fields = ['amount', 'payment_type']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError('Amount must be greater than 0')
        return amount


# =========================================================
# NOTIFICATION FORMS
# =========================================================

class NotificationForm(forms.ModelForm):
    
    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'notification_type': forms.Select(attrs={'class': 'form-control'}),
        }


# =========================================================
# GRIEVANCE FORMS
# =========================================================

class GrievanceForm(forms.ModelForm):
    """Form for users to submit grievances"""
    
    class Meta:
        model = Grievance
        fields = ['subject', 'description', 'attachment']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subject'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Describe your grievance in detail'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_subject(self):
        subject = self.cleaned_data.get('subject')
        if subject and len(subject) < 5:
            raise ValidationError('Subject must be at least 5 characters long')
        return subject

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description) < 20:
            raise ValidationError('Please provide a detailed description (at least 20 characters)')
        return description


class GrievanceAdminForm(forms.ModelForm):
    """Form for admin to update grievance status with resolution remarks"""
    
    class Meta:
        model = Grievance
        fields = ['status', 'resolution_remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'resolution_remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Add resolution remarks here...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        resolution_remarks = cleaned_data.get('resolution_remarks')
        
        # If status is RESOLVED, resolution remarks are required
        if status == 'RESOLVED' and not resolution_remarks:
            raise ValidationError('Resolution remarks are required when resolving a grievance')
        
        return cleaned_data