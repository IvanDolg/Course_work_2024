import logging

from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied
from django.utils.timezone import now
from datetime import datetime, timedelta

from kuser.models import Reader

logger = logging.getLogger('main')


class ExclusionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        allowed_url = reverse('admin:logout')
        allowed_url_rereg = reverse('admin:kuser_reregistration_add')

        if request.path == allowed_url:
            return

        if request.path == allowed_url_rereg:
            return

        if request.user.is_authenticated:
            try:
                reader = Reader.objects.get(user=request.user)
                if hasattr(request.user, 'reader') and reader.exclusion:
                    raise PermissionDenied("Ваш доступ к системе ограничен.")
                if reader.ticket_expiration is not None:
                    delta = reader.ticket_expiration - now().date()
                    if delta.days < 0 and not reader.exclusion:
                        return render(request, 'kuser/ticket_expired.html', {
                            'reregistration_url': reverse('admin:kuser_reregistration_add')
                        })


            except Reader.DoesNotExist:
                pass


class CustomLoginRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path == reverse('admin:index') and request.user.is_authenticated:
            return redirect('profile')
        return response
    