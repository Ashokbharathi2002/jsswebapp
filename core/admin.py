from django.contrib import admin
from .models import CustomUser, SolarInstallationProject, Attendance, Complaint, Notice, Quotation, LeaveRequest, Notification, NotificationRead

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_approved', 'employee_id')
    list_filter = ('role', 'is_approved')
    search_fields = ('username', 'email', 'employee_id')

@admin.register(SolarInstallationProject)
class SolarInstallationProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'staff_incharge', 'status', 'total_value')
    list_filter = ('status',)
    search_fields = ('title', 'customer__username', 'staff_incharge__username')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('user__username',)

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('customer', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__username', 'subject')

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'content', 'author__username')

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'lead_name', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'customer__username', 'lead_name', 'lead_email')


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by', 'created_at')
    list_filter = ('status', 'leave_type', 'start_date', 'end_date')
    search_fields = ('user__username', 'reason')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_broadcast', 'notification_type', 'created_at')
    list_filter = ('notification_type', 'is_broadcast', 'created_at')
    search_fields = ('title', 'message', 'user__username')


@admin.register(NotificationRead)
class NotificationReadAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('user__username', 'notification__title')





