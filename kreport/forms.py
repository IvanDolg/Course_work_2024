import datetime
import logging
from calendar import monthrange

from django import forms

from klib.models import BaseFundElement
from kreport.document_generator import get_month_name
from kreport.models import CreateInventoryBook, CreateWorkplaceReport, UserAccounting, CreateDebtorsReport, \
    BookCirculationReport
from kuser.models import Organization, Position, Reader

logger = logging.getLogger('main')


class CreateInventoryBookForm(forms.ModelForm):
    first_inventory_number = forms.ModelChoiceField(
        queryset=BaseFundElement.objects.none(),
        label='Первый инвентарный номер',
        required=False
    )
    last_inventory_number = forms.ModelChoiceField(
        queryset=BaseFundElement.objects.none(),
        label='Последний инвентарный номер',
        required=False
    )

    class Meta:
        model = CreateInventoryBook
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance: CreateInventoryBook = self.instance

        if instance.pk:
            queryset = BaseFundElement.objects.all()

            if instance.all_edition:
                self.fields['first_inventory_number'].queryset = queryset
                self.fields['last_inventory_number'].queryset = queryset

            elif instance.display_excluded_editions:
                filtered_queryset = queryset.filter(publication_status=BaseFundElement.PUBLICATION_STATUS_WRITTEN_OFF)
                self.fields['first_inventory_number'].queryset = filtered_queryset
                self.fields['last_inventory_number'].queryset = filtered_queryset

            elif instance.display_current_editions:
                filtered_queryset = queryset.filter(
                    publication_status=BaseFundElement.PUBLICATION_STATUS_NOT_WRITTEN_OFF)
                self.fields['first_inventory_number'].queryset = filtered_queryset
                self.fields['last_inventory_number'].queryset = filtered_queryset

            if instance.template_type:
                self.fields['first_inventory_number'].queryset = self.fields['first_inventory_number'].queryset.filter(
                    arrival__order_edition__edition__edition_subtype=instance.template_type
                )
                self.fields['last_inventory_number'].queryset = self.fields['last_inventory_number'].queryset.filter(
                    arrival__order_edition__edition__edition_subtype=instance.template_type
                )
        else:
            self.fields['first_inventory_number'].queryset = BaseFundElement.objects.none()
            self.fields['last_inventory_number'].queryset = BaseFundElement.objects.none()

    def clean_first_inventory_number(self):
        first_inventory_number = self.cleaned_data['first_inventory_number']
        return first_inventory_number.id if first_inventory_number else None

    def clean_last_inventory_number(self):
        last_inventory_number = self.cleaned_data['last_inventory_number']
        return last_inventory_number.id if last_inventory_number else None


class OrganisationForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        label='Организация',
        required=False,
        widget=forms.Select
    )

    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        label='Должность',
        required=False,
        widget=forms.Select
    )

    class Meta:
        model = CreateWorkplaceReport
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organization'].queryset = Organization.objects.all()
        self.fields['position'].queryset = Position.objects.all()

    def clean_edition(self):
        organization = self.cleaned_data['organization']
        position = self.cleaned_data['position']
        return organization.id if organization else None


class UserAccountingForm(forms.ModelForm):
    class Meta:
        model = UserAccounting
        fields = ['report_type', 'year', 'month', 'day']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        year = self.initial.get('year') or datetime.date.today().year
        month = self.initial.get('month') or 1

        try:
            days_in_month = monthrange(int(year), int(month))[1]
        except ValueError:
            days_in_month = 31

        self.fields['month'] = forms.ChoiceField(
            choices=[(0, 'Все месяцы')] + [(i, get_month_name(i)) for i in range(1, 13)],
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'}),
            label="Месяц"

        )

        self.fields['day'] = forms.ChoiceField(
            choices=[(0, 'Весь месяц')] + [(i, i) for i in range(1, days_in_month + 1)],
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'}),
            label="День"

        )

    def clean_day(self):
        day = self.cleaned_data.get('day')
        if day == '0':
            return None
        return day

    def clean_month(self):
        month = self.cleaned_data.get('month')
        if month == 0:
            return None
        return month


    class Media:
        js = ('js/dynamic_days.js',)


class DebtorsForm(forms.ModelForm):
    reader_id = forms.ModelChoiceField(
        queryset=Reader.objects.using('belrw-user-db').all(),
        label='Читатель',
        required=False,
        widget=forms.Select
    )

    class Meta:
        model = CreateDebtorsReport
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reader_id'].queryset = Reader.objects.using('belrw-user-db').all()

    def clean_reader_id(self):
        reader = self.cleaned_data['reader_id']
        return reader.id if reader else None


class CirculationForm(forms.ModelForm):
    reader_id = forms.ModelChoiceField(
        queryset=Reader.objects.using('belrw-user-db').all(),
        label='Читатель',
        required=False,
        widget=forms.Select
    )

    class Meta:
        model = BookCirculationReport
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reader_id'].queryset = Reader.objects.using('belrw-user-db').all()

    def clean_reader_id(self):
        reader = self.cleaned_data['reader_id']
        return reader.id if reader else None
