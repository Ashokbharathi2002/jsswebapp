from django.contrib import admin
from .models import CustomUser, SolarInstallationProject, Attendance, Complaint, Note, Notice, Quotation

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

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('title', 'user__username')

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



