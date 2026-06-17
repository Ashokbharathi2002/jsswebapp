from django.urls import path
from django.shortcuts import redirect
from . import views
from . import views_notifications

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
    path('dashboard/supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    
    # Admin actions
    path('admin/approve/<int:user_id>/', views.admin_approve_customer, name='admin_approve_customer'),
    path('admin/revoke/<int:user_id>/', views.admin_revoke_customer, name='admin_revoke_customer'),
    path('admin/attendance/export/', views.export_attendance_csv, name='export_attendance_csv'),
    path('admin/projects/export/', views.export_projects_csv, name='export_projects_csv'),
    path('admin/salaries/export/', views.export_salaries_csv, name='export_salaries_csv'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('notices/create/', views.create_notice_view, name='create_notice'),
    path('notices/delete/<int:notice_id>/', views.delete_notice_view, name='delete_notice'),
    path('quotations/add/', views.add_quotation_view, name='add_quotation'),
    path('quotations/edit/<int:quote_id>/', views.edit_quotation_view, name='edit_quotation'),
    path('quotations/delete/<int:quote_id>/', views.delete_quotation_view, name='delete_quotation'),
    path('quotations/view/<int:quote_id>/', views.view_quotation_proposal_view, name='view_quotation_proposal'),
    
    # Expenses CRUD
    path('expenses/add/', views.add_expense_view, name='add_expense'),
    path('expenses/edit/<int:expense_id>/', views.edit_expense_view, name='edit_expense'),
    path('expenses/delete/<int:expense_id>/', views.delete_expense_view, name='delete_expense'),
    
    # Notifications APIs and views
    path('notifications/api/unread/', views_notifications.notification_api_unread, name='notification_api_unread'),
    path('notifications/read/<int:notification_id>/', views_notifications.mark_notification_read, name='mark_notification_read'),
    path('notifications/read/all/', views_notifications.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/push/', views_notifications.push_notification_view, name='push_notification'),
    
    # Inspection Workflow
    path('inspections/', views.inspection_list, name='inspection_list'),
    path('inspections/<int:inspection_id>/', views.inspection_detail, name='inspection_detail'),
    path('inspections/<int:inspection_id>/perform/', views.perform_inspection, name='perform_inspection'),
]


