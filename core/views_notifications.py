from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db import models
from .models import Notification, NotificationRead, CustomUser

@login_required
def notification_api_unread(request):
    """
    Returns a JSON array of all unread notifications targeting the current user or broadcast,
    along with the unread count.
    """
    user = request.user
    # Get IDs of notifications read by this user
    read_ids = NotificationRead.objects.filter(user=user).values_list('notification_id', flat=True)
    
    # Retrieve unread notifications (targeted to user, or broadcasted)
    unread_notifications = Notification.objects.filter(
        models.Q(user=user) | models.Q(is_broadcast=True)
    ).exclude(id__in=read_ids).order_by('-created_at')
    
    data = []
    for notification in unread_notifications:
        data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_broadcast': notification.is_broadcast,
        })
        
    return JsonResponse({
        'count': len(data),
        'notifications': data
    })

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """
    Marks a specific notification as read for the current user.
    """
    user = request.user
    notification = get_object_or_404(
        Notification, 
        models.Q(user=user) | models.Q(is_broadcast=True),
        id=notification_id
    )
    
    # Create a read record if it doesn't already exist
    NotificationRead.objects.get_or_create(user=user, notification=notification)
    
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def mark_all_notifications_read(request):
    """
    Marks all notifications targeting the current user or broadcast as read.
    """
    user = request.user
    read_ids = NotificationRead.objects.filter(user=user).values_list('notification_id', flat=True)
    
    # Find all unread notifications
    unread_notifications = Notification.objects.filter(
        models.Q(user=user) | models.Q(is_broadcast=True)
    ).exclude(id__in=read_ids)
    
    # Create NotificationRead instances for all of them
    read_records = [
        NotificationRead(user=user, notification=notification)
        for notification in unread_notifications
    ]
    NotificationRead.objects.bulk_create(read_records, ignore_conflicts=True)
    
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def push_notification_view(request):
    """
    Allows Admins and Superusers to manually push (broadcast or direct) a notification.
    """
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Admins/Super Users Only")
        
    title = request.POST.get('title', '').strip()
    message = request.POST.get('message', '').strip()
    notification_type = request.POST.get('notification_type', 'INFO').strip()
    recipient = request.POST.get('recipient', 'all_users').strip()
    
    if title and message:
        if recipient == 'all_users':
            # Broadcast to all users
            Notification.objects.create(
                title=title,
                message=message,
                notification_type=notification_type,
                is_broadcast=True
            )
            messages.success(request, "Broadcast notification pushed successfully!")
        else:
            try:
                user_id = int(recipient)
                target_user = get_object_or_404(CustomUser, id=user_id)
                Notification.objects.create(
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    user=target_user
                )
                messages.success(request, f"Push notification sent successfully to user '{target_user.username}'!")
            except ValueError:
                messages.error(request, "Invalid recipient selected.")
    else:
        messages.error(request, "Failed to push notification. Title and message cannot be empty.")
        
    next_url = request.META.get('HTTP_REFERER', 'dashboard')
    return redirect(next_url)
