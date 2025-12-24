from django.urls import path
from . import views
from .views import send_test_whatsapp

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('info/', views.info_view, name='info'),
    
    # This is the NEW verification page (replaces send-otp)
    path('verify-otp/', views.verify_otp_page, name='verify_otp_page'),
    path("send-whatsapp/", send_test_whatsapp),
    path('portal-admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve-test/<int:record_id>/<str:result>/', views.approve_test_action, name='approve_test'),
    path('approve-vaccine/<int:record_id>/', views.approve_vaccine, name='approve_vaccine'),
]