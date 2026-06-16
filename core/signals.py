from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    LoginLog, CustomUser, SolarInstallationProject, LeaveRequest, 
    Complaint, Quotation, ProjectExpense, Notice, Notification
)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    if request is not None:
        # Retrieve IP address, checking proxy headers first
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Retrieve browser/device User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Save to logs table
        LoginLog.objects.create(
            user=user,
            ip_address=ip,
            user_agent=user_agent
        )
    else:
        # Handle cases where request object is not provided (e.g. unit tests / management commands)
        LoginLog.objects.create(
            user=user,
            ip_address=None,
            user_agent=None
        )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user is not None:
        # Retrieve the latest login log for this user that doesn't have a logout time yet
        latest_log = LoginLog.objects.filter(user=user, logout_time__isnull=True).order_by('-login_time').first()
        if latest_log:
            latest_log.logout_time = timezone.now()
            latest_log.save()


# User Registration & Approval
@receiver(pre_save, sender=CustomUser)
def user_pre_save(sender, instance, **kwargs):
    if instance.id:
        try:
            old_instance = CustomUser.objects.get(id=instance.id)
            instance._old_is_approved = old_instance.is_approved
        except CustomUser.DoesNotExist:
            instance._old_is_approved = None
    else:
        instance._old_is_approved = None

@receiver(post_save, sender=CustomUser)
def user_post_save(sender, instance, created, **kwargs):
    if created:
        if not instance.is_approved:
            # Notify all admins and superusers
            admins = CustomUser.objects.filter(role__in=['ADMIN', 'SUPERUSER'], is_active=True)
            for admin in admins:
                Notification.objects.create(
                    title="New Registration Pending Approval",
                    message=f"User '{instance.username}' ({instance.get_role_display()}) registered and is awaiting admin approval.",
                    notification_type="ALERT",
                    user=admin
                )
        else:
            # User was created already approved
            Notification.objects.create(
                title="Welcome to Jothi Solar Solutions",
                message="Your account has been set up successfully. Welcome aboard!",
                notification_type="SUCCESS",
                user=instance
            )
    else:
        old_is_approved = getattr(instance, '_old_is_approved', None)
        if old_is_approved is False and instance.is_approved is True:
            Notification.objects.create(
                title="Account Approved",
                message="Your account has been approved by the Administrator. You can now access all dashboard features.",
                notification_type="SUCCESS",
                user=instance
            )


# Project Milestones
@receiver(pre_save, sender=SolarInstallationProject)
def project_pre_save(sender, instance, **kwargs):
    if instance.id:
        try:
            old_instance = SolarInstallationProject.objects.get(id=instance.id)
            instance._old_status = old_instance.status
            instance._old_staff = old_instance.staff_incharge
        except SolarInstallationProject.DoesNotExist:
            instance._old_status = None
            instance._old_staff = None
    else:
        instance._old_status = None
        instance._old_staff = None

@receiver(post_save, sender=SolarInstallationProject)
def project_post_save(sender, instance, created, **kwargs):
    from .models import Inverter
    Inverter.objects.get_or_create(project=instance)

    if created:
        # Notify Customer
        Notification.objects.create(
            title="Solar Project Configured",
            message=f"Your project '{instance.title}' has been successfully configured.",
            notification_type="SUCCESS",
            user=instance.customer
        )
        # Notify Staff
        if instance.staff_incharge:
            Notification.objects.create(
                title="New Project Assignment",
                message=f"You have been assigned as the staff in-charge for project '{instance.title}' for customer {instance.customer.get_full_name() or instance.customer.username}.",
                notification_type="INFO",
                user=instance.staff_incharge
            )
        # Notify Admins/Superusers
        admins = CustomUser.objects.filter(role__in=['ADMIN', 'SUPERUSER'], is_active=True)
        for admin in admins:
            Notification.objects.create(
                title="New Project Dispatch",
                message=f"New solar installation project '{instance.title}' configured for customer {instance.customer.username}.",
                notification_type="INFO",
                user=admin
            )
    else:
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            # Notify Customer
            status_display = instance.get_status_display()
            Notification.objects.create(
                title="Project Status Updated",
                message=f"Your project '{instance.title}' status has changed to '{status_display}'.",
                notification_type="INFO",
                user=instance.customer
            )
            # Notify Staff
            if instance.staff_incharge:
                Notification.objects.create(
                    title="Project Status Updated",
                    message=f"Project '{instance.title}' status has changed to '{status_display}'.",
                    notification_type="INFO",
                    user=instance.staff_incharge
                )
            # Notify Admins
            admins = CustomUser.objects.filter(role__in=['ADMIN', 'SUPERUSER'], is_active=True)
            for admin in admins:
                Notification.objects.create(
                    title="Project Stage Change",
                    message=f"Project '{instance.title}' status has changed to '{status_display}'.",
                    notification_type="ACTIVITY",
                    user=admin
                )

        old_staff = getattr(instance, '_old_staff', None)
        if old_staff != instance.staff_incharge:
            if instance.staff_incharge:
                Notification.objects.create(
                    title="Assigned to Project",
                    message=f"You have been assigned as the staff in-charge for project '{instance.title}'.",
                    notification_type="INFO",
                    user=instance.staff_incharge
                )
            if old_staff:
                Notification.objects.create(
                    title="Project Reassigned",
                    message=f"You are no longer assigned to project '{instance.title}'.",
                    notification_type="ALERT",
                    user=old_staff
                )

    # Auto-schedule 6-month inspection if status becomes COMPLETED
    if instance.status == 'COMPLETED':
        from .models import Inspection
        if not Inspection.objects.filter(project=instance).exists():
            import datetime
            closing_date = instance.closing_date or timezone.now().date()
            month = closing_date.month - 1 + 6
            year = closing_date.year + month // 12
            month = month % 12 + 1
            day = min(closing_date.day, [31,
                29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
            scheduled_date = datetime.date(year, month, day)
            
            Inspection.objects.create(
                project=instance,
                scheduled_date=scheduled_date,
                status='SCHEDULED'
            )


# Complaints Inbox
@receiver(pre_save, sender=Complaint)
def complaint_pre_save(sender, instance, **kwargs):
    if instance.id:
        try:
            old_instance = Complaint.objects.get(id=instance.id)
            instance._old_status = old_instance.status
        except Complaint.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Complaint)
def complaint_post_save(sender, instance, created, **kwargs):
    if created:
        # Notify Admins/Superusers
        admins = CustomUser.objects.filter(role__in=['ADMIN', 'SUPERUSER'], is_active=True)
        for admin in admins:
            Notification.objects.create(
                title="New Complaint Filed",
                message=f"Client '{instance.customer.username}' filed a complaint: '{instance.subject}'.",
                notification_type="ALERT",
                user=admin
            )
    else:
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            if instance.status == 'RESOLVED':
                Notification.objects.create(
                    title="Complaint Resolved",
                    message=f"Your complaint '{instance.subject}' has been resolved by our administrative team.",
                    notification_type="SUCCESS",
                    user=instance.customer
                )


# Leave Requests
@receiver(pre_save, sender=LeaveRequest)
def leave_request_pre_save(sender, instance, **kwargs):
    if instance.id:
        try:
            old_instance = LeaveRequest.objects.get(id=instance.id)
            instance._old_status = old_instance.status
        except LeaveRequest.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=LeaveRequest)
def leave_request_post_save(sender, instance, created, **kwargs):
    if created:
        # Notify Admins/Superusers
        admins = CustomUser.objects.filter(role__in=['ADMIN', 'SUPERUSER'], is_active=True)
        for admin in admins:
            Notification.objects.create(
                title="New Leave Request",
                message=f"{instance.user.get_full_name() or instance.user.username} requested {instance.get_leave_type_display()} from {instance.start_date} to {instance.end_date}.",
                notification_type="ALERT",
                user=admin
            )
    else:
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            status_display = instance.get_status_display()
            notification_type = "SUCCESS" if instance.status == "APPROVED" else "ALERT"
            Notification.objects.create(
                title=f"Leave Request {status_display}",
                message=f"Your leave request for {instance.get_leave_type_display()} from {instance.start_date} to {instance.end_date} has been {status_display.lower()}.",
                notification_type=notification_type,
                user=instance.user
            )


# Quotations / Proposals
@receiver(pre_save, sender=Quotation)
def quotation_pre_save(sender, instance, **kwargs):
    if instance.id:
        try:
            old_instance = Quotation.objects.get(id=instance.id)
            instance._old_status = old_instance.status
        except Quotation.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Quotation)
def quotation_post_save(sender, instance, created, **kwargs):
    if created:
        if instance.status == 'SENT' and instance.customer:
            Notification.objects.create(
                title="New Quotation Received",
                message=f"A solar system proposal '{instance.title}' has been generated and sent to you.",
                notification_type="INFO",
                user=instance.customer
            )
    else:
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            if instance.status == 'SENT' and instance.customer:
                Notification.objects.create(
                    title="New Quotation Received",
                    message=f"A solar system proposal '{instance.title}' has been generated and sent to you.",
                    notification_type="INFO",
                    user=instance.customer
                )
            elif instance.status in ['ACCEPTED', 'REJECTED'] and instance.customer:
                # Notify creator & admins
                recipients = list(CustomUser.objects.filter(role__in=['ADMIN', 'SUPERUSER'], is_active=True))
                if instance.created_by not in recipients:
                    recipients.append(instance.created_by)
                for r in recipients:
                    Notification.objects.create(
                        title=f"Quotation {instance.get_status_display()}",
                        message=f"Quotation '{instance.title}' for client '{instance.customer.username}' has been {instance.get_status_display().lower()}.",
                        notification_type="SUCCESS" if instance.status == 'ACCEPTED' else "ALERT",
                        user=r
                    )


# Project Expenses
@receiver(post_save, sender=ProjectExpense)
def expense_post_save(sender, instance, created, **kwargs):
    if created:
        # Notify Customer
        Notification.objects.create(
            title="New Project Expense Recorded",
            message=f"A new expense '{instance.title}' of ₹{instance.amount} was recorded for your project '{instance.project.title}'.",
            notification_type="INFO",
            user=instance.project.customer
        )
        # Notify Admins & Superusers
        admins = CustomUser.objects.filter(role__in=['ADMIN', 'SUPERUSER'], is_active=True)
        for admin in admins:
            Notification.objects.create(
                title="Project Expense Recorded",
                message=f"Worker '{instance.created_by.username}' recorded a ₹{instance.amount} expense ('{instance.title}') for project '{instance.project.title}'.",
                notification_type="ACTIVITY",
                user=admin
            )


# Announcement Notices
@receiver(post_save, sender=Notice)
def notice_post_save(sender, instance, created, **kwargs):
    if created and instance.is_active:
        Notification.objects.create(
            title=f"New Announcement: {instance.title}",
            message=instance.content,
            notification_type="SUCCESS",
            is_broadcast=True
        )
