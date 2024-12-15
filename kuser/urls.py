import profile
from django.urls import path
from django.views.generic import TemplateView
from . import views
from .views import (
    activate, OrganizationAutocomplete, DepartmentAutocomplete,
    JobPositionAutocomplete, password_recovery, password_reset_confirm,
    update_profile, get_education_types, change_password, change_email,
    worker_register, other_natural_person_reg, profile, activate_other_natural_person, user_register,
    download_filled_doc, reregister, verify_password, re_registration, confirmation_message
)

urlpatterns = [
    path('register/', user_register, name='register'),
    path('worker-register/', worker_register, name='worker_register'),
    path('verify-password/', verify_password, name='verify_password'),
    path('other-natural-person-register/', other_natural_person_reg, name='other_natural_person_register'),
    path('password_recovery/', password_recovery, name='password_recovery'),
    path('re-registration/', re_registration, name='re_registration'),
    path('create-password/<uidb64>/<token>/', activate, name='create_password'),
    path('create-password/change/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
    path('create-password/activate/<uidb64>/<token>/', activate_other_natural_person, name='activate_other_natural_person'),
    path('admin/confirmation/', confirmation_message, name='confirmation_message'),

    # This url for email-sender registration
    # path('register/activate/<uidb64>/<token>', activate, name='activate'),
    # This url for email-sender password recovery
    # path('reset_password/update/<uidb64>/<token>', password_reset_confirm, name='password_reset_confirm'),

    path('update_password_success/', TemplateView.as_view(template_name='registration/update_password_success.html'),
         name='update_password_success'),
    path('register/success/', TemplateView.as_view(template_name='registration/register_success.html'),
         name='register_success'),
    path('register/foget_password/', TemplateView.as_view(template_name='registration/foget_password.html'),
         name='forget_password'),
    path('register/update_password/', TemplateView.as_view(template_name='registration/update_password.html'),
         name='update_password'),
    path('admin/', TemplateView.as_view(template_name='admin/login.html'),
         name='login'),
    path('register/organization-autocomplete/', OrganizationAutocomplete.as_view(create_field='name'),
         name='organization-autocomplete'),
    path('register/department-autocomplete/', DepartmentAutocomplete.as_view(create_field='name'),
         name='department-autocomplete'),
    path('register/job-position-autocomplete/', JobPositionAutocomplete.as_view(create_field='name'),
         name='job-position-autocomplete'),
    path('register/education-autocomplete/', get_education_types, name='education-autocomplete'),

    path('admin/update-profile/', update_profile, name='update_profile'),

    path('register/change-password/', change_password, name='change_password'),
    path('register/change-email/', change_email, name='change_email'),

    path('admin/profile/', profile, name='profile'),

    path('admin/kuser/download-creds/', download_filled_doc, name='download_filled_doc'),

    path('admin/kuser/reregister/', reregister, name='reregister'),
]