# base/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Web Pages (HTML)
    path('', views.home_view, name='home'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register-page'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('my-bids/', views.my_bids_page, name='my-bids-page'),
    path('tenders/', views.tender_list_view, name='tender-list-web'),
    path('tenders/<slug:slug>/', views.tender_detail_view, name='tender-detail-web'),
    path('auctions/', views.auction_list_view, name='auction-list-web'),
    path('auctions/<slug:slug>/', views.auction_detail_view, name='auction-detail-web'),
    path('lands/', views.land_list_view, name='land-list-web'),
    path('lands/<slug:slug>/', views.land_detail_view, name='land-detail-web'),
    
    # API endpoints
    path('api/register/', views.register_user, name='register'),
    path('api/login/', views.login_user, name='api-login'),
    path('api/logout/', views.logout_user, name='logout'),
    path('api/profile/', views.user_profile, name='profile'),
    path('api/change-password/', views.change_password, name='change-password'),
    path('api/dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('api/users/', views.list_users, name='users'),
    path('api/users/<int:user_id>/', views.manage_user, name='manage-user'),
    path('api/users/<int:user_id>/verify/', views.verify_user, name='verify-user'),
    path('api/departments/', views.department_list, name='departments'),
    path('api/departments/<int:department_id>/', views.department_detail, name='department-detail'),
    path('api/lands/', views.land_list, name='lands-api'),
    path('api/lands/<int:land_id>/', views.land_detail, name='land-detail-api'),
    path('api/tenders/', views.tender_list, name='tenders-api'),
    path('api/tenders/<int:tender_id>/', views.tender_detail, name='tender-detail-api'),
    path('api/tenders/export/csv/', views.export_tenders_csv, name='export-tenders'),
    path('api/auctions/', views.auction_list, name='auctions-api'),
    path('api/auctions/<int:auction_id>/', views.auction_detail, name='auction-detail-api'),
    path('api/auctions/<int:auction_id>/bids/', views.auction_bids, name='auction-bids'),
    path('api/my-bids/', views.my_bids, name='my-bids'),
    path('api/my-documents/', views.my_documents, name='my-documents'),
    path('api/documents/<int:document_id>/verify/', views.verify_document, name='verify-document'),
    path('api/contracts/', views.contract_list, name='contracts'),
    path('api/contracts/<int:contract_id>/', views.contract_detail, name='contract-detail'),
    path('api/payments/', views.payment_list, name='payments'),
    path('api/payments/<int:payment_id>/', views.payment_detail, name='payment-detail'),
    path('api/notifications/', views.notification_list, name='notifications'),
    path('api/notifications/mark-read/', views.mark_notification_read, name='mark-read'),
    path('api/notifications/<int:notification_id>/delete/', views.delete_notification, name='delete-notification'),
    path('api/grievances/', views.grievance_list, name='grievances'),
    path('api/grievances/<int:grievance_id>/', views.grievance_detail, name='grievance-detail'),
    path('api/search/', views.global_search, name='search'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)