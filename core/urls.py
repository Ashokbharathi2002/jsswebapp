from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    # Homepage redirects to login
    path('', lambda request: redirect('login'), name='home'),
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
    
    # Dashboards
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path('dashboard/staff/', views.staff_dashboard, name='staff_dashboard'),
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/superuser/', views.superuser_dashboard, name='superuser_dashboard'),
    
    # Admin actions
    path('admin/approve/<int:user_id>/', views.admin_approve_customer, name='admin_approve_customer'),
    path('admin/revoke/<int:user_id>/', views.admin_revoke_customer, name='admin_revoke_customer'),
]
