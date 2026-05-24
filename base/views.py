# base/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Count, Avg, Min, Max
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
import json
import uuid
from datetime import datetime, timedelta
import csv
import logging
import random

# Rest Framework imports
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

# Local imports
from .models import *
from .forms import *
from .serializers import *

# Set up logging
logger = logging.getLogger(__name__)


# =========================================================
# HELPER FUNCTIONS & DECORATORS
# =========================================================

def is_super_admin(user):
    return user.is_authenticated and user.role == 'SUPER_ADMIN'

def is_government_officer(user):
    return user.is_authenticated and user.role in ['SUPER_ADMIN', 'GOVERNMENT_OFFICER']

def is_tender_publisher(user):
    return user.is_authenticated and user.role in ['SUPER_ADMIN', 'GOVERNMENT_OFFICER', 'TENDER_PUBLISHER']

def is_auctioneer(user):
    return user.is_authenticated and user.role in ['SUPER_ADMIN', 'AUCTIONEER']

def is_bidder(user):
    return user.is_authenticated and user.role in ['BIDDER', 'CONTRACTOR']

def send_notification(user, title, message, notification_type='GENERAL'):
    """Helper function to create notifications"""
    try:
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type
        )
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# =========================================================
# WEB PAGE VIEWS (HTML Templates)
# =========================================================

def login_page(request):
    """Render the login page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'base/login.html')

def register_page(request):
    """Render the registration page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'base/register.html')

def home_view(request):
    """Home page view"""
    context = {
        'total_lands': LandRecord.objects.count(),
        'active_tenders': Tender.objects.filter(end_date__gt=timezone.now(), tender_status='OPEN').count(),
        'live_auctions': Auction.objects.filter(auction_status='LIVE').count(),
        'recent_tenders': Tender.objects.filter(tender_status='OPEN').order_by('-created_at')[:5],
        'recent_auctions': Auction.objects.filter(auction_status='LIVE').order_by('-created_at')[:5],
    }
    return render(request, 'base/home.html', context)

def tender_list_view(request):
    """Tender list page"""
    tenders = Tender.objects.filter(tender_status='OPEN').order_by('-created_at')
    
    form = TenderSearchForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('query'):
            tenders = tenders.filter(title__icontains=form.cleaned_data['query'])
        if form.cleaned_data.get('department'):
            tenders = tenders.filter(department=form.cleaned_data['department'])
    
    paginator = Paginator(tenders, 12)
    page = request.GET.get('page', 1)
    
    try:
        tenders = paginator.page(page)
    except PageNotAnInteger:
        tenders = paginator.page(1)
    except EmptyPage:
        tenders = paginator.page(paginator.num_pages)
    
    context = {
        'tenders': tenders,
        'form': form,
    }
    return render(request, 'base/tender_list.html', context)

def tender_detail_view(request, slug):
    """Tender detail page"""
    tender = get_object_or_404(Tender, slug=slug)
    context = {'tender': tender}
    return render(request, 'base/tender_detail.html', context)

def auction_list_view(request):
    """Auction list page"""
    auctions = Auction.objects.filter(auction_status='LIVE').order_by('-created_at')
    
    paginator = Paginator(auctions, 12)
    page = request.GET.get('page', 1)
    
    try:
        auctions = paginator.page(page)
    except PageNotAnInteger:
        auctions = paginator.page(1)
    except EmptyPage:
        auctions = paginator.page(paginator.num_pages)
    
    context = {'auctions': auctions}
    return render(request, 'base/auction_list.html', context)

def auction_detail_view(request, slug):
    """Auction detail page"""
    auction = get_object_or_404(Auction, slug=slug)
    context = {
        'auction': auction,
    }
    return render(request, 'base/auction_detail.html', context)

def land_list_view(request):
    """Land records list page"""
    lands = LandRecord.objects.filter(status='AVAILABLE').order_by('-created_at')
    
    form = LandSearchForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('query'):
            lands = lands.filter(
                Q(land_title__icontains=form.cleaned_data['query']) |
                Q(location__icontains=form.cleaned_data['query'])
            )
        if form.cleaned_data.get('district'):
            lands = lands.filter(district__icontains=form.cleaned_data['district'])
        if form.cleaned_data.get('min_price'):
            lands = lands.filter(market_value__gte=form.cleaned_data['min_price'])
        if form.cleaned_data.get('max_price'):
            lands = lands.filter(market_value__lte=form.cleaned_data['max_price'])
    
    paginator = Paginator(lands, 12)
    page = request.GET.get('page', 1)
    
    try:
        lands = paginator.page(page)
    except PageNotAnInteger:
        lands = paginator.page(1)
    except EmptyPage:
        lands = paginator.page(paginator.num_pages)
    
    context = {
        'lands': lands,
        'form': form,
    }
    return render(request, 'base/land_list.html', context)

def land_detail_view(request, slug):
    """Land record detail page"""
    land = get_object_or_404(LandRecord, slug=slug)
    context = {'land': land}
    return render(request, 'base/land_detail.html', context)

@login_required
def dashboard_view(request):
    """User dashboard"""
    context = {
        'user': request.user,
        'notifications': Notification.objects.filter(user=request.user, is_read=False)[:10],
        'unread_notifications_count': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'base/dashboard.html', context)

@login_required
def my_bids_page(request):
    """My Bids page - HTML view for viewing all bids with pagination"""
    return render(request, 'base/my_bids.html')


# =========================================================
# AUTHENTICATION API VIEWS
# =========================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """User registration API view"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                user = serializer.save()
                
                send_notification(
                    user, 
                    'Welcome to GovConnect', 
                    f'Welcome {user.username}! Your account has been created successfully.',
                    'GENERAL'
                )
                
                logger.info(f"New user registered: {user.username}")
                
                return Response({
                    'message': 'User registered successfully',
                    'user': CustomUserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response({
                'error': 'Registration failed. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Unified login view - GET redirects to login page, POST processes API login"""
    if request.method == 'GET':
        return redirect('/login/')
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Please provide both username and password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        if not user.is_active:
            return Response({
                'error': 'Your account is inactive. Please contact administrator.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        login(request, user)
        
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        logger.info(f"User logged in: {user.username}")
        
        return Response({
            'message': 'Login successful',
            'user': CustomUserSerializer(user).data,
            'role': user.role
        }, status=status.HTTP_200_OK)
    else:
        logger.warning(f"Failed login attempt for username: {username}")
        return Response({
            'error': 'Invalid credentials. Please check your username and password.'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """User logout view - Accepts both GET and POST"""
    try:
        username = request.user.username
        auth_logout(request)
        logger.info(f"User logged out: {username}")
        
        if request.method == 'GET':
            return redirect('/login/?logout=success')
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        if request.method == 'GET':
            return redirect('/login/')
        return Response({
            'error': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get or update user profile"""
    if request.method == 'GET':
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password"""
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not request.user.check_password(old_password):
        return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
    
    if new_password != confirm_password:
        return Response({'error': 'New passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.set_password(new_password)
    request.user.save()
    
    from django.contrib.auth import update_session_auth_hash
    update_session_auth_hash(request, request.user)
    
    return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


# =========================================================
# DASHBOARD API VIEWS
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics based on user role"""
    user = request.user
    
    if user.role == 'SUPER_ADMIN':
        stats = {
            'total_users': CustomUser.objects.count(),
            'total_lands': LandRecord.objects.count(),
            'total_tenders': Tender.objects.count(),
            'total_auctions': Auction.objects.count(),
            'total_bids': Bid.objects.count(),
            'total_payments': Payment.objects.aggregate(total=Sum('amount'))['total'] or 0,
            'active_tenders': Tender.objects.filter(end_date__gt=timezone.now(), tender_status='OPEN').count(),
            'live_auctions': Auction.objects.filter(
                auction_start_time__lte=timezone.now(), 
                auction_end_time__gte=timezone.now(), 
                auction_status='LIVE'
            ).count(),
            'pending_grievances': Grievance.objects.filter(status='OPEN').count(),
            'pending_verifications': DocumentVerification.objects.filter(verification_status='PENDING').count(),
            'revenue_last_month': Payment.objects.filter(
                payment_date__gte=timezone.now() - timedelta(days=30),
                payment_status='SUCCESS'
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
    elif user.role == 'GOVERNMENT_OFFICER':
        stats = {
            'total_tenders': Tender.objects.filter(published_by=user).count(),
            'total_auctions': Auction.objects.filter(created_by=user).count(),
            'active_tenders': Tender.objects.filter(
                published_by=user, 
                end_date__gt=timezone.now(), 
                tender_status='OPEN'
            ).count(),
            'pending_verifications': DocumentVerification.objects.filter(verification_status='PENDING').count(),
        }
    elif user.role == 'BIDDER':
        stats = {
            'my_bids': Bid.objects.filter(bidder=user).count(),
            'winning_bids': Bid.objects.filter(bidder=user, bid_status='WINNING').count(),
            'total_spent': Payment.objects.filter(user=user, payment_status='SUCCESS').aggregate(total=Sum('amount'))['total'] or 0,
            'active_bids': Bid.objects.filter(bidder=user, auction__auction_end_time__gt=timezone.now()).count(),
        }
    else:
        stats = {
            'total_lands': LandRecord.objects.count(),
            'total_tenders': Tender.objects.filter(tender_status='OPEN').count(),
            'live_auctions': Auction.objects.filter(auction_status='LIVE').count(),
        }
    
    return Response(stats)


# =========================================================
# USER MANAGEMENT API VIEWS (Admin only)
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_super_admin)
def list_users(request):
    """List all users with filtering"""
    users = CustomUser.objects.all()
    
    role = request.query_params.get('role')
    if role:
        users = users.filter(role=role)
    
    is_verified = request.query_params.get('is_verified')
    if is_verified:
        users = users.filter(is_verified=is_verified.lower() == 'true')
    
    search = request.query_params.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    paginator = PageNumberPagination()
    paginator.page_size = request.query_params.get('page_size', 20)
    result_page = paginator.paginate_queryset(users, request)
    serializer = CustomUserSerializer(result_page, many=True)
    
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_super_admin)
def manage_user(request, user_id):
    """Get, update or delete a specific user"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'GET':
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserDetailSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'User updated successfully',
                'user': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_super_admin)
def verify_user(request, user_id):
    """Verify a user account"""
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_verified = True
    user.save()
    
    send_notification(
        user,
        'Account Verified',
        'Your account has been verified by the administrator.',
        'GENERAL'
    )
    
    return Response({'message': 'User verified successfully'})


# =========================================================
# DEPARTMENT API VIEWS
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def department_list(request):
    """List all departments or create new"""
    
    if request.method == 'GET':
        departments = Department.objects.all().annotate(tender_count=Count('tenders'))
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if not is_government_officer(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            department = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def department_detail(request, department_id):
    """Get, update or delete a specific department"""
    department = get_object_or_404(Department, id=department_id)
    
    if request.method == 'GET':
        serializer = DepartmentSerializer(department)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not is_government_officer(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = DepartmentSerializer(department, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not is_super_admin(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        department.delete()
        return Response({'message': 'Department deleted successfully'})


# =========================================================
# LAND RECORD API VIEWS
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def land_list(request):
    """List all land records or create new"""
    
    if request.method == 'GET':
        lands = LandRecord.objects.select_related('category').all()
        
        category_id = request.query_params.get('category')
        if category_id:
            lands = lands.filter(category_id=category_id)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            lands = lands.filter(status=status_filter)
        
        search = request.query_params.get('search')
        if search:
            lands = lands.filter(
                Q(land_title__icontains=search) |
                Q(location__icontains=search)
            )
        
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 20)
        result_page = paginator.paginate_queryset(lands, request)
        serializer = LandRecordSerializer(result_page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        if not is_government_officer(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = LandRecordSerializer(data=request.data)
        if serializer.is_valid():
            land = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def land_detail(request, land_id):
    """Get, update or delete a specific land record"""
    land = get_object_or_404(LandRecord, id=land_id)
    
    if request.method == 'GET':
        serializer = LandRecordDetailSerializer(land, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not is_government_officer(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = LandRecordSerializer(land, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not is_super_admin(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        land.delete()
        return Response({'message': 'Land record deleted successfully'})


# =========================================================
# TENDER API VIEWS
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tender_list(request):
    """List all tenders or create new"""
    
    if request.method == 'GET':
        tenders = Tender.objects.select_related('department', 'published_by').all()
        
        status_filter = request.query_params.get('status')
        if status_filter:
            tenders = tenders.filter(tender_status=status_filter)
        
        search = request.query_params.get('search')
        if search:
            tenders = tenders.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 20)
        result_page = paginator.paginate_queryset(tenders, request)
        serializer = TenderSerializer(result_page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        if not is_tender_publisher(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data.copy()
        data['published_by'] = request.user.id
        
        serializer = TenderSerializer(data=data)
        if serializer.is_valid():
            tender = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def tender_detail(request, tender_id):
    """Get, update or delete a specific tender"""
    tender = get_object_or_404(Tender, id=tender_id)
    
    if request.method == 'GET':
        serializer = TenderSerializer(tender)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not is_tender_publisher(request.user) and tender.published_by != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TenderSerializer(tender, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not is_super_admin(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        tender.delete()
        return Response({'message': 'Tender deleted successfully'})


# =========================================================
# AUCTION API VIEWS
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def auction_list(request):
    """List all auctions or create new"""
    
    if request.method == 'GET':
        auctions = Auction.objects.select_related('land', 'created_by').all()
        
        status_filter = request.query_params.get('status')
        if status_filter:
            auctions = auctions.filter(auction_status=status_filter)
        
        search = request.query_params.get('search')
        if search:
            auctions = auctions.filter(
                Q(auction_title__icontains=search) |
                Q(land__land_title__icontains=search)
            )
        
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 20)
        result_page = paginator.paginate_queryset(auctions, request)
        serializer = AuctionListSerializer(result_page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        if not is_auctioneer(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data.copy()
        data['created_by'] = request.user.id
        
        serializer = AuctionSerializer(data=data)
        if serializer.is_valid():
            auction = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def auction_detail(request, auction_id):
    """Get, update or delete a specific auction"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    if request.method == 'GET':
        serializer = AuctionSerializer(auction)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not is_auctioneer(request.user) and auction.created_by != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AuctionSerializer(auction, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not is_super_admin(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        auction.delete()
        return Response({'message': 'Auction deleted successfully'})


# =========================================================
# BID API VIEWS - COMPLETE WORKING VERSION
# =========================================================

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .models import Auction, Bid
from .serializers import BidSerializer

# Send notification function
def send_notification(user, title, message, notification_type='GENERAL'):
    """Helper function to create notifications"""
    try:
        from .models import Notification
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type
        )
    except Exception as e:
        print(f"Failed to send notification: {e}")


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def auction_bids(request, auction_id):
    """
    List bids for an auction or place new bid
    - GET: Returns all bids for this auction
    - POST: Places a new bid (or updates existing bid)
    """
    auction = get_object_or_404(Auction, id=auction_id)
    
    # GET request - return all bids
    if request.method == 'GET':
        bids = auction.bids.select_related('bidder').all().order_by('-bid_amount')
        serializer = BidSerializer(bids, many=True)
        return Response({
            'count': bids.count(),
            'results': serializer.data
        })
    
    # POST request - place a new bid
    elif request.method == 'POST':
        print("=" * 60)
        print("BID PLACEMENT ATTEMPT")
        print(f"Auction ID: {auction_id}")
        print(f"Auction Title: {auction.auction_title}")
        print(f"User: {request.user.username}")
        print(f"User Role: {request.user.role}")
        
        try:
            # 1. Authorization checks
            if request.user.role not in ['BIDDER', 'CONTRACTOR']:
                return Response({
                    'error': 'Only bidders and contractors can place bids'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if auction is live
            if not auction.is_live():
                return Response({
                    'error': 'Auction is not active. Please check the auction start and end times.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user is bidding on their own auction
            if auction.created_by == request.user:
                return Response({
                    'error': 'You cannot bid on your own auction'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Get and validate bid amount
            bid_amount = request.data.get('bid_amount')
            if bid_amount is None:
                return Response({
                    'error': 'Bid amount is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                bid_amount = float(bid_amount)
            except (ValueError, TypeError):
                return Response({
                    'error': 'Invalid bid amount. Please enter a valid number.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"Bid Amount: {bid_amount}")
            
            # 3. Calculate current highest and minimum allowed bid
            current_highest = auction.current_highest_bid
            if current_highest is None or current_highest == 0:
                current_highest = auction.reserve_price
            
            min_allowed = current_highest + auction.minimum_increment_amount
            
            print(f"Current Highest: {current_highest}")
            print(f"Min Allowed: {min_allowed}")
            print(f"Reserve Price: {auction.reserve_price}")
            print(f"Increment: {auction.minimum_increment_amount}")
            
            # 4. Validate bid amount against rules
            if bid_amount < auction.reserve_price:
                return Response({
                    'error': f'Bid must be at least the reserve price of ₹{auction.reserve_price:,.2f}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if bid_amount <= current_highest:
                return Response({
                    'error': f'Bid must be higher than current highest bid of ₹{current_highest:,.2f}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if bid_amount < min_allowed:
                return Response({
                    'error': f'Minimum bid allowed is ₹{min_allowed:,.2f} (Current highest ₹{current_highest:,.2f} + Increment ₹{auction.minimum_increment_amount:,.2f})'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 5. Place or update bid atomically
            with transaction.atomic():
                # Lock the auction row to prevent race conditions
                auction = Auction.objects.select_for_update().get(id=auction_id)
                
                # Re-check auction status after lock
                if not auction.is_live():
                    return Response({
                        'error': 'Auction is not active'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check if user already has a bid
                existing_bid = Bid.objects.filter(auction=auction, bidder=request.user).first()
                
                if existing_bid:
                    # Update existing bid
                    print(f"Updating existing bid from {existing_bid.bid_amount} to {bid_amount}")
                    existing_bid.bid_amount = bid_amount
                    existing_bid.bid_status = 'WINNING'
                    existing_bid.save(update_fields=['bid_amount', 'bid_status'])
                    bid = existing_bid
                else:
                    # Create new bid
                    print("Creating new bid")
                    bid = Bid.objects.create(
                        auction=auction,
                        bidder=request.user,
                        bid_amount=bid_amount,
                        bid_status='WINNING'
                    )
                
                # Mark all other bids as LOST (except this one)
                auction.bids.filter(bid_status='WINNING').exclude(id=bid.id).update(bid_status='LOST')
                
                # Update auction's current highest bid
                auction.current_highest_bid = bid_amount
                auction.save(update_fields=['current_highest_bid'])
                print(f"Updated auction.current_highest_bid to {bid_amount}")
            
            # 6. Send notification to auction creator
            try:
                send_notification(
                    auction.created_by,
                    f'New Bid on {auction.auction_title}',
                    f'{request.user.username} placed a bid of ₹{bid_amount:,.2f}',
                    'BID'
                )
                print("Notification sent to auction creator")
            except Exception as e:
                print(f"Notification error (non-critical): {e}")
            
            # 7. Return success response
            return Response({
                'message': 'Bid placed successfully!' if not existing_bid else 'Bid updated successfully!',
                'bid': {
                    'id': bid.id,
                    'bidder_name': request.user.username,
                    'bid_amount': bid_amount,
                    'submitted_at': bid.submitted_at.isoformat(),
                    'bid_status': 'WINNING'
                },
                'current_highest_bid': float(bid_amount)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"ERROR placing bid: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'Server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bids(request):
    """Get current user's bids"""
    bids = Bid.objects.filter(bidder=request.user).select_related('auction', 'auction__land').order_by('-submitted_at')
    
    paginator = PageNumberPagination()
    paginator.page_size = request.query_params.get('page_size', 20)
    result_page = paginator.paginate_queryset(bids, request)
    serializer = BidSerializer(result_page, many=True)
    
    return paginator.get_paginated_response(serializer.data)

# =========================================================
# DOCUMENT VERIFICATION API VIEWS
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def my_documents(request):
    """List user's documents or upload new"""
    
    if request.method == 'GET':
        documents = DocumentVerification.objects.filter(user=request.user)
        serializer = DocumentVerificationSerializer(documents, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = DocumentVerificationSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_government_officer)
def verify_document(request, document_id):
    """Verify or reject a document"""
    document = get_object_or_404(DocumentVerification, id=document_id)
    
    serializer = DocumentVerifySerializer(document, data=request.data, partial=True)
    if serializer.is_valid():
        document = serializer.save(verified_by=request.user, verified_at=timezone.now())
        return Response(DocumentVerificationSerializer(document).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================================================
# CONTRACT API VIEWS
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def contract_list(request):
    """List contracts or create new"""
    
    if request.method == 'GET':
        if request.user.role == 'CONTRACTOR':
            contracts = Contract.objects.filter(contractor=request.user)
        else:
            contracts = Contract.objects.all()
        
        serializer = ContractSerializer(contracts, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if not is_government_officer(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ContractSerializer(data=request.data)
        if serializer.is_valid():
            contract = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def contract_detail(request, contract_id):
    """Get or update contract details"""
    contract = get_object_or_404(Contract, id=contract_id)
    
    if request.method == 'GET':
        serializer = ContractSerializer(contract)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not is_government_officer(request.user):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ContractSerializer(contract, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================================================
# PAYMENT API VIEWS
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def payment_list(request):
    """List payments or create new"""
    
    if request.method == 'GET':
        if request.user.role == 'SUPER_ADMIN':
            payments = Payment.objects.all()
        else:
            payments = Payment.objects.filter(user=request.user)
        
        payments = payments.order_by('-payment_date')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data.copy()
        data['user'] = request.user.id
        
        serializer = CreatePaymentSerializer(data=data)
        if serializer.is_valid():
            payment = serializer.save(payment_status='SUCCESS')
            return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_detail(request, payment_id):
    """Get payment details"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.user.role != 'SUPER_ADMIN' and payment.user != request.user:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = PaymentSerializer(payment)
    return Response(serializer.data)


# =========================================================
# NOTIFICATION API VIEWS
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """Get user's notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = PageNumberPagination()
    paginator.page_size = request.query_params.get('page_size', 20)
    result_page = paginator.paginate_queryset(notifications, request)
    serializer = NotificationSerializer(result_page, many=True)
    
    return paginator.get_paginated_response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request):
    """Mark notifications as read"""
    notification_ids = request.data.get('notification_ids', [])
    mark_all = request.data.get('mark_all', False)
    
    if mark_all:
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
    else:
        Notification.objects.filter(
            user=request.user,
            id__in=notification_ids
        ).update(is_read=True, read_at=timezone.now())
    
    return Response({'message': 'Notifications marked as read'})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    return Response({'message': 'Notification deleted successfully'})


# =========================================================
# GRIEVANCE API VIEWS
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def grievance_list(request):
    """List grievances or create new"""
    
    if request.method == 'GET':
        if request.user.role == 'SUPER_ADMIN':
            grievances = Grievance.objects.all()
        else:
            grievances = Grievance.objects.filter(user=request.user)
        
        grievances = grievances.order_by('-created_at')
        serializer = GrievanceSerializer(grievances, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data.copy()
        data['user'] = request.user.id
        
        serializer = GrievanceCreateSerializer(data=data)
        if serializer.is_valid():
            grievance = serializer.save(user=request.user)
            return Response(GrievanceSerializer(grievance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def grievance_detail(request, grievance_id):
    """Get or update grievance status"""
    grievance = get_object_or_404(Grievance, id=grievance_id)
    
    if request.method == 'GET':
        serializer = GrievanceSerializer(grievance)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not is_super_admin(request.user):
            return Response({'error': 'Only admin can update grievance status'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = GrievanceUpdateSerializer(grievance, data=request.data, partial=True)
        if serializer.is_valid():
            grievance = serializer.save()
            if grievance.status == 'RESOLVED' and not grievance.resolved_at:
                grievance.resolved_at = timezone.now()
                grievance.save()
            return Response(GrievanceSerializer(grievance).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================================================
# SEARCH API VIEWS
# =========================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def global_search(request):
    """Global search across all models"""
    query = request.query_params.get('q', '')
    
    if not query:
        return Response({'error': 'Search query required'}, status=status.HTTP_400_BAD_REQUEST)
    
    results = {
        'lands': LandRecordSerializer(LandRecord.objects.filter(
            Q(land_title__icontains=query) | Q(location__icontains=query)
        )[:10], many=True).data,
        'tenders': TenderListSerializer(Tender.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )[:10], many=True).data,
        'auctions': AuctionListSerializer(Auction.objects.filter(
            Q(auction_title__icontains=query) | Q(land__land_title__icontains=query)
        )[:10], many=True).data,
    }
    
    return Response(results)


# =========================================================
# EXPORT API VIEWS
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_government_officer)
def export_tenders_csv(request):
    """Export tenders to CSV"""
    tenders = Tender.objects.select_related('department', 'published_by').all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tenders_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Department', 'Budget', 'Start Date', 'End Date', 'Status'])
    
    for tender in tenders:
        writer.writerow([
            tender.tender_id,
            tender.title,
            tender.department.department_name,
            tender.project_budget,
            tender.start_date,
            tender.end_date,
            tender.tender_status
        ])
    
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_government_officer)
def export_payments_csv(request):
    """Export payments to CSV"""
    payments = Payment.objects.select_related('user').all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Transaction ID', 'User', 'Amount', 'Type', 'Status', 'Date'])
    
    for payment in payments:
        writer.writerow([
            payment.transaction_id,
            payment.user.username,
            payment.amount,
            payment.get_payment_type_display(),
            payment.payment_status,
            payment.payment_date
        ])
    
    return response