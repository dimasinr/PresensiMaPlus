from django.utils import timezone
 
def global_context(request):
    """Add global context variables to all templates"""
    return {
        'today': timezone.now().date(),
    } 