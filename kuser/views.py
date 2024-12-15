import logging
from django.contrib.admin import AdminSite
from django.contrib.auth import logout, authenticate

from dal import autocomplete
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from django.http import HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from itsdangerous import URLSafeTimedSerializer
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import render, redirect
from django.contrib import messages
import requests

from docx import Document
import io

from datetime import datetime, timedelta
from django.utils import timezone

from config.settings.base import SECRET_KEY, SECURITY_PASSWORD_SALT
from kuser.constants import EDUCATION_TYPE
from .document_generator import generate_password_document
from .forms import ReaderCreationForm, ReaderCreationPasswordForm, PasswordRecoveryForm, PasswordCreationPasswordForm, \
    ProfileForm, convert_education_type, ChangeEmailForm, WorkerCreationForm, OtherNaturalPersonForm
from .models import Organization, Department, Position, MyUser, Reader, AbstractUser, Worker, OtherNaturalPerson

logger = logging.getLogger('main')


# Иное физическое лицо (рег)
def other_natural_person_reg(request):
    if request.method == 'POST':
        form = OtherNaturalPersonForm(request.POST)
        if form.is_valid():
            other_natural_person = form.save()

            uid = urlsafe_base64_encode(force_bytes(other_natural_person.user.pk))
            token = generate_confirmation_token(other_natural_person.user.pk)

            return redirect(reverse('activate_other_natural_person', kwargs={'uidb64': uid, 'token': token}))
        else:
            logger.debug(form.errors)
            return render(request, 'registration/orher_natural_person_registration.html', {'form': form})
    else:
        form = OtherNaturalPersonForm()

    return render(request, 'registration/orher_natural_person_registration.html', {'form': form})

@login_required
def verify_password(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = authenticate(request, username=request.user.username, password=password)
        if user is not None:
            return redirect(reverse('worker_register'))
        else:
            return render(request, 'registration/verify_password.html', {'error': 'Неверный пароль'})
    return render(request, 'registration/verify_password.html')

# Рабочий (рег)
def worker_register(request):
    if request.method == 'POST':
        form = WorkerCreationForm(request.POST)
        if form.is_valid():
            worker = form.save()

            uid = urlsafe_base64_encode(force_bytes(worker.user.pk))
            token = generate_confirmation_token(worker.user.pk)

            return redirect(reverse('create_password', kwargs={'uidb64': uid, 'token': token}))
        else:
            logger.debug(form.errors)
            return render(request, 'registration/worker_registration.html', {'form': form})
    else:
        form = WorkerCreationForm()

    return render(request, 'registration/worker_registration.html', {'form': form})


def generate_confirmation_token(user_pk):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(user_pk, salt=SECURITY_PASSWORD_SALT)


# Страница для создания пароля
def user_register(request):
    if request.method == 'POST':
        form = ReaderCreationForm(request.POST)
        if form.is_valid():
            reader = form.save()

            uid = urlsafe_base64_encode(force_bytes(reader.user.pk))
            token = generate_confirmation_token(reader.user.pk)

            request.session['uidb64'] = uid
            request.session['token'] = token

            return redirect('confirmation_message')

        return render(request, 'registration/user_registration.html', {'form': form})

    form = ReaderCreationForm()
    return render(request, 'registration/user_registration.html', {'form': form})


def confirmation_message(request):
    return render(request, 'registration/confirmation_message.html')

# Этот код для отправки URL-адреса на электронную почту и создания нового пароля
# def register(request):
#     if request.method == 'POST':
#         form = ReaderCreationForm(request.POST)
#         if form.is_valid():
#             reader = form.save()
#             reader.save()
#
#             current_site = get_current_site(request)
#             email_subject = "Confirm your Email @ BelRW - Django Login!!"
#             message2 = render_to_string('registration/email_confirmation.html', {
#                 'name': reader.user.first_name,
#                 'domain': current_site.domain,
#                 'uid': urlsafe_base64_encode(force_bytes(reader.user.pk)),
#                 'token': generate_confirmation_token(reader.user.pk)
#             })
#             response = requests.post(
#                 url='https://belrw.krainet.by/notification/api/v2/email',
#                 headers={'Content-Type': 'application/json'},
#                 json={
#                     'subject': email_subject,
#                     'text': message2,
#                     'to': [
#                         {
#                             'email': reader.user.email
#                         }
#                     ]
#                 }
#             )
#
#             return redirect('success/')
#         else:
#             return render(request, 'registration/user_registration.html', {'form': form})
#     else:
#         form = ReaderCreationForm()
#
#     return render(request, 'registration/user_registration.html', {'form': form})


# Восстановление пароля
def password_recovery(request):
    if request.method == 'POST':
        form = PasswordRecoveryForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = MyUser.objects.get(email=email)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = generate_confirmation_token(user.pk)

            return redirect(reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))
        else:
            return render(request, 'registration/update_password.html', {'form': form})
    else:
        form = PasswordRecoveryForm()

    return render(request, 'registration/update_password.html', {'form': form})

# Этот код для отправки URL-адреса на электронную почту, для восстановления пароля
# def password_recovery(request):
#     if request.method == 'POST':
#         form = PasswordRecoveryForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             user = MyUser.objects.get(email=email)
#
#             current_site = get_current_site(request)
#             email_subject = "Восстановление пароля @ BelRW"
#             message = render_to_string('registration/password_reset_email.html', {
#                 'domain': current_site.domain,
#                 'uid': urlsafe_base64_encode(force_bytes(user.pk)),
#                 'token': generate_confirmation_token(user.pk)
#             })
#
#             response = requests.post(
#                 url='https://belrw.krainet.by/notification/api/v2/email',
#                 headers={'Content-Type': 'application/json'},
#                 json={
#                     'subject': email_subject,
#                     'text': message,
#                     'to': [{'email': user.email}]
#                 }
#             )
#
#             return redirect('update_password_success')
#     else:
#         form = PasswordRecoveryForm()
#
#     return render(request, 'registration/update_password.html', {'form': form})


# Активация для рабочего, пользователя
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = MyUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
        user = None

    if user is not None and user.pk == int(uid):
        if request.method == 'POST':
            form = ReaderCreationPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['password1'])
                user.is_active = True
                user.is_staff = True
                user.save()
                return redirect('/admin')

        else:
            username = user.username
            initial_data = {'username': username}
            form = ReaderCreationPasswordForm(initial=initial_data)

        return render(request, 'registration/create_password.html', {
            'form': form,
            'username': user.username
        })
    else:
        return render(request, 'activation_failed.html')


# Активация для иного физ лица
def activate_other_natural_person(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = MyUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
        user = None

    if user is not None and user.pk == int(uid):
        if request.method == 'POST':
            form = ReaderCreationPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['password1'])
                user.is_active = True
                user.is_staff = True
                user.save()

                password = form.cleaned_data['password1']
                document = generate_password_document(user, password)

                if document:
                    response = HttpResponse(document,
                                            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    response['Content-Disposition'] = f'attachment; filename="credentials_{user.username}.docx"'
                    return response

                else:
                    return HttpResponse("Ошибка генерации документа.", status=500)
        else:
            username = user.username
            initial_data = {'username': username}
            form = ReaderCreationPasswordForm(initial=initial_data)

        return render(request, 'registration/create_password_other_natural_person.html', {
            'form': form,
            'username': user.username
        })
    else:
        return render(request, 'activation_failed.html')


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = MyUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
        user = None

    if user is not None and user.pk == int(uid):
        if request.method == 'POST':
            form = ReaderCreationPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['password1'])
                user.is_active = True
                user.is_staff = True
                user.save()
                return redirect(reverse('admin:index'))
        else:
            initial_data = {'username': user.username}
            form = ReaderCreationPasswordForm(initial=initial_data)
        return render(request, 'registration/refresh_password.html', {
            'form': form,
            'username': user.username
        })
    else:
        return render(request, 'activation_failed.html')


def signout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("signin")


def signout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("signin")


class OrganizationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Organization.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class DepartmentAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Department.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class JobPositionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Position.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


def get_education_types(request):
    education_types = [name for _, name in EDUCATION_TYPE]
    results = [
        {
            "id": str(index + 1),
            "text": name,
            "selected_text": name
        }
        for index, name in enumerate(education_types)
    ]
    data = {
        "results": results,
        "pagination": {
            "more": False
        }
    }
    return JsonResponse(data, json_dumps_params={'ensure_ascii': False, 'indent': 4})


class MyAdminSite(AdminSite):
    @method_decorator(never_cache)
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}

        user = request.user
        reader = Reader.objects.filter(user=user).first()
        if reader is None:
            reader = Worker.objects.filter(user=user).first()
        elif reader is None:
            reader = OtherNaturalPerson.objects.filter(user=user).first()
        if reader is None:
            reader = MyUser.objects.filter(username=user).first()
        if reader is None:
            reader = None

        if reader is not None:
            if type(reader) == Reader or type(reader) == Worker or type(reader) == OtherNaturalPerson:
                extra_context['reader_info'] = reader.to_dict_info()
            extra_context['reader_auth'] = reader.to_dict_auth()

        # return render(request, 'admin/profile.html', extra_context)
        return super().index(request, extra_context=extra_context)


def profile(request, extra_context=None):
    extra_context = extra_context or {}

    user = request.user
    reader = Reader.objects.filter(user=user).first()
    if reader is None:
        reader = Worker.objects.filter(user=user).first()
    elif reader is None:
        reader = OtherNaturalPerson.objects.filter(user=user).first()
    if reader is None:
        reader = MyUser.objects.filter(username=user).first()
    if reader is None:
        reader = None

    if reader is not None:
        if type(reader) == Reader or type(reader) == Worker or type(reader) == OtherNaturalPerson:
            extra_context['reader_info'] = reader.to_dict_info()
        extra_context['reader_auth'] = reader.to_dict_auth()

    return render(request, 'admin/profile.html', extra_context)


def update_profile(request):
    if request.method == 'POST':
        form = convert_education_type(request)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'}, status=200)
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        form = ProfileForm()
    return render(request, 'admin/index.html', {'form': form})


def change_password(request):
    if request.method == 'POST':
        user = MyUser.objects.get(username=request.POST.get('username'))
        form = PasswordCreationPasswordForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'ok', 'errors': form.errors}, status=200)
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


def change_email(request):
    logger.debug("HERE")
    if request.method == 'POST':
        user = MyUser.objects.get(username=request.POST.get('username'))
        form = ChangeEmailForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'ok', 'errors': form.errors}, status=200)
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


def download_filled_doc(request):
    doc = Document('kuser/DocFile/Иное_физическое_лицо_креды.docx')

    username = request.user.username
    password = 'ваш_пароль'

    for paragraph in doc.paragraphs:
        if '{{ username }}' in paragraph.text:
            paragraph.text = paragraph.text.replace('{{ username }}', username)
        if '{{ password }}' in paragraph.text:
            paragraph.text = paragraph.text.replace('{{ password }}', password)

    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)

    response = HttpResponse(file_stream, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="filled_template.docx"'

    return response


def reregister(request):
    logger.debug('alo')
    if request.method == 'GET':
        readers = Reader.objects.all()
        today = timezone.now().date()
        for reader in readers:
            delta = reader.ticket_expiration - today
            if delta.days < 14 and reader.email_send == True:
                logger.debug(f'{reader}')
                email_subject = "Требование к перерегистрации "
                message2 = (f'Ваш срок действия билета заканчивается {reader.ticket_expiration}. Вам необходимо перерегистрироваться.'
                            f' Перерегистрация проходит в библиотеке к которой вы приписаны')
                response = requests.post(
                    url='https://belrw.krainet.by/notification/api/v2/email',
                    headers={'Content-Type': 'application/json'},
                    json={
                        'subject': email_subject,
                        'text': message2,
                        'to': [
                            {
                                'email': reader.user.email
                            }
                        ]
                    }
                )
                logger.debug(f'{reader.email_send}')
                reader.email_send = False
                logger.debug(f'{reader.email_send}')
                reader.save()
                logger.debug(f'{response}')
    return HttpResponse('success')


def re_registration(request):
    user = request.user
    user.date_joined = timezone.now()
    user.validity_period = timezone.now().replace(month=12, day=31)
    user.save()
    messages.success(request, 'Ваши данные успешно обновлены!')
    return redirect(reverse('admin:kuser_myuser_change', args=[user.pk]))

