from .models import Notice, Quotation


def active_notices(request):
    """
    Context processor to make active notices available globally in all templates.
    """
    return {
        'active_notices': Notice.objects.filter(is_active=True).order_by('-created_at')
    }

def admin_quotations(request):
    """
    Context processor to make quotations available on the dashboards.
    - Admins/Superusers see all quotations.
    - Clients (Customers) see only finalized quotations (Sent, Accepted, Rejected) assigned to them.
    """
    if not request.user.is_authenticated:
        return {'all_quotations': [], 'client_quotations': []}
    
    if request.user.role in ['ADMIN', 'SUPERUSER'] or request.user.is_superuser:
        return {
            'all_quotations': Quotation.objects.all().order_by('-created_at')
        }
    elif request.user.role == 'CUSTOMER':
        return {
            'client_quotations': Quotation.objects.filter(customer=request.user, status__in=['SENT', 'ACCEPTED', 'REJECTED']).order_by('-created_at')
        }
    return {'all_quotations': [], 'client_quotations': []}


