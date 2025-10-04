from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_gatepass_notification(gatepass):
    """
    Send email notification to parent when a new gatepass request is created
    """
    subject = 'New Gatepass Request'
    approve_url = f"{settings.SITE_URL}/api/approval/{gatepass.token}/approve/"
    reject_url = f"{settings.SITE_URL}/api/approval/{gatepass.token}/reject/"
    
    context = {
        'student_name': gatepass.student.user.get_full_name(),
        'purpose': gatepass.purpose,
        'date': gatepass.request_date,
        'approve_url': approve_url,
        'reject_url': reject_url,
    }
    
    html_message = render_to_string('gatepass/email/gatepass_request.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [gatepass.student.parent.email],
        html_message=html_message,
        fail_silently=False,
    )