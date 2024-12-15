import logging
from django import forms
from django.core.exceptions import ValidationError

from kuser.models import Worker
from .models import BaseFundElement, PeriodicalOrder, PeriodicalEdition, NewspaperOrder, JournalOrder, NonPeriodicalOrderElement, ReplaceEdition, ReplacementAct, \
    WriteOffAct, DepositoryFundElement, BaseEdition
from django.utils.translation import gettext_lazy as _

from .validators import validate_year

logger = logging.getLogger(__name__)


class PeriodicalOrderForm(forms.ModelForm):
    edition_year = forms.IntegerField(label=_('Year'), initial=0, validators=[validate_year])
    duration_of_receipt_years = forms.IntegerField(required=False, label=_('Years of receipt'), initial=0)
    duration_of_receipt_months = forms.ChoiceField(choices=[(str(i), str(i)) for i in range(0, 12)],
                                                   label=_('Months of receipt'), initial=0)
    duration_of_storage_years = forms.IntegerField(required=False, label=_('Years of storage'), initial=0)
    duration_of_storage_months = forms.ChoiceField(choices=[(str(i), str(i)) for i in range(0, 12)],
                                                   label=_('Months of storage'), initial=0)

    class Meta:
        model = PeriodicalOrder
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['edition_year'].initial = self.instance.edition.year if self.instance.edition else ''
            self.fields['duration_of_receipt_years'].initial = self.instance.duration_of_receipt // 12
            self.fields['duration_of_receipt_months'].initial = self.instance.duration_of_receipt % 12
            self.fields['duration_of_storage_years'].initial = self.instance.duration_of_storage // 12
            self.fields['duration_of_storage_months'].initial = self.instance.duration_of_storage % 12

    def clean(self):
        cleaned_data = super().clean()
        duration_of_receipt_years = cleaned_data.get('duration_of_receipt_years', 0)
        duration_of_receipt_months = int(cleaned_data.get('duration_of_receipt_months', 0))
        duration_of_storage_years = cleaned_data.get('duration_of_storage_years', 0)
        duration_of_storage_months = int(cleaned_data.get('duration_of_storage_months', 0))
        first_number = int(cleaned_data.get('first_number', 0))
        last_number = int(cleaned_data.get('last_number', 0))

        if last_number < first_number:
            raise forms.ValidationError(
                _('Last number (%(last_number)d) must not be less than first number (%(first_number)d).'),
                params={'last_number': last_number, 'first_number': first_number},
            )

        if (duration_of_receipt_years == 0 and duration_of_receipt_months == 0
                or duration_of_storage_years == 0 and duration_of_storage_months == 0):
            raise forms.ValidationError(_('Duration of receipt must be greater than 0.'))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        duration_of_receipt_years = self.cleaned_data['duration_of_receipt_years']
        duration_of_receipt_months = int(self.cleaned_data['duration_of_receipt_months'])
        duration_of_storage_years = self.cleaned_data['duration_of_storage_years']
        duration_of_storage_months = int(self.cleaned_data['duration_of_storage_months'])

        instance.duration_of_storage = duration_of_storage_months + duration_of_storage_years * 12
        instance.duration_of_receipt = duration_of_receipt_months + duration_of_receipt_years * 12

        if commit:
            instance.save()
        return instance


class JournalOrderForm(PeriodicalOrderForm):
    edition = forms.ModelChoiceField(
        label=_('Edition'),
        queryset=PeriodicalEdition.objects.filter(edition_subtype='MAGAZINES'),
        empty_label=_('Select an edition'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['edition'].initial = self.instance.edition

    class Meta:
        model = JournalOrder
        fields = '__all__'


class NewspaperOrderForm(PeriodicalOrderForm):
    edition = forms.ModelChoiceField(
        label=_('Edition'),
        queryset=PeriodicalEdition.objects.filter(edition_subtype='NEWSPAPERS'),
        empty_label=_('Select an edition'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['edition'].initial = self.instance.edition

    class Meta(JournalOrderForm.Meta):
        model = NewspaperOrder
        fields = JournalOrderForm.Meta.fields

    def save(self, commit=True):
        instance = super().save(commit)

        return instance


class NonPeriodicalOrderElementForm(forms.ModelForm):
    class Meta:
        model = NonPeriodicalOrderElement
        fields = ['edition', 'number_of_copies', 'price', 'vat_rate']
        labels = {
            'edition': 'Издание',
            'number_of_copies': 'Количество копий',
            'price': 'Стоимость',
            'vat_rate': 'Ставка НДС',
        }


class WriteOffActForm(forms.ModelForm):
    chairman = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Председатель комиссии',
        required=True,
        widget=forms.Select
    )
    vice_chairman = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Зам. председателя комиссии',
        required=True,
        widget=forms.Select
    )
    member_1 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 1',
        required=True,
        widget=forms.Select
    )
    member_2 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 2',
        required=True,
        widget=forms.Select
    )
    member_3 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 3',
        required=True,
        widget=forms.Select
    )
    submitted_by = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Списанные документы сдал(а)',
        required=True,
        widget=forms.Select
    )
    registered_by = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='В книге суммарного учета акт проведен',
        required=True,
        widget=forms.Select
    )

    class Meta:
        model = WriteOffAct
        exclude = []

    def clean(self):
        cleaned_data = super().clean()

        if self.instance:
            total_excluded = self.instance.total_excluded
        else:
            total_excluded = 0

        socio_economic_count = cleaned_data.get('socio_economic_count', 0)
        technical_count = cleaned_data.get('technical_count', 0)
        other_count = cleaned_data.get('other_count', 0)
        railway_theme_count = cleaned_data.get('railway_theme_count', 0)

        total_count = socio_economic_count + technical_count + other_count + railway_theme_count

        if total_count > total_excluded:
            raise ValidationError(
                'Сумма полей "Социально-экономическое количество", '
                '"Техническое количество", "Прочее количество" и '
                '"Количество по железнодорожной тематике" не должна превышать общее количество исключенных.'
            )

        if 'chairman' in cleaned_data:
            cleaned_data['chairman'] = cleaned_data['chairman'].id

        if 'vice_chairman' in cleaned_data:
            cleaned_data['vice_chairman'] = cleaned_data['vice_chairman'].id

        if 'member_1' in cleaned_data:
            cleaned_data['member_1'] = cleaned_data['member_1'].id

        if 'member_2' in cleaned_data:
            cleaned_data['member_2'] = cleaned_data['member_2'].id

        if 'member_3' in cleaned_data:
            cleaned_data['member_3'] = cleaned_data['member_3'].id

        if 'submitted_by' in cleaned_data:
            cleaned_data['submitted_by'] = cleaned_data['submitted_by'].id

        if 'registered_by' in cleaned_data:
            cleaned_data['registered_by'] = cleaned_data['registered_by'].id

        return cleaned_data


class WriteOffActFormTest(forms.ModelForm):
    chairman = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Председатель комиссии',
        required=True,
        widget=forms.Select
    )
    vice_chairman = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Зам. председателя комиссии',
        required=True,
        widget=forms.Select
    )
    member_1 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 1',
        required=True,
        widget=forms.Select
    )
    member_2 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 2',
        required=True,
        widget=forms.Select
    )
    member_3 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 3',
        required=True,
        widget=forms.Select
    )
    submitted_by = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Списанные документы сдал(а)',
        required=True,
        widget=forms.Select
    )
    registered_by = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='В книге суммарного учета акт проведен',
        required=True,
        widget=forms.Select
    )

    class Meta:
        model = WriteOffAct
        exclude = []

    def clean(self):
        cleaned_data = super().clean()

        if self.instance:
            total_excluded = self.instance.total_excluded
        else:
            total_excluded = 0

        socio_economic_count = cleaned_data.get('socio_economic_count', 0)
        technical_count = cleaned_data.get('technical_count', 0)
        other_count = cleaned_data.get('other_count', 0)
        railway_theme_count = cleaned_data.get('railway_theme_count', 0)

        total_count = socio_economic_count + technical_count + other_count + railway_theme_count

        if total_count > total_excluded:
            raise ValidationError(
                'Сумма полей "Социально-экономическое количество", '
                '"Техническое количество", "Прочее количество" и '
                '"Количество по железнодорожной тематике" не должна превышать общее количество исключенных.'
            )

        if 'chairman' in cleaned_data:
            cleaned_data['chairman'] = cleaned_data['chairman'].id

        if 'vice_chairman' in cleaned_data:
            cleaned_data['vice_chairman'] = cleaned_data['vice_chairman'].id

        if 'member_1' in cleaned_data:
            cleaned_data['member_1'] = cleaned_data['member_1'].id

        if 'member_2' in cleaned_data:
            cleaned_data['member_2'] = cleaned_data['member_2'].id

        if 'member_3' in cleaned_data:
            cleaned_data['member_3'] = cleaned_data['member_3'].id

        if 'submitted_by' in cleaned_data:
            cleaned_data['submitted_by'] = cleaned_data['submitted_by'].id

        if 'registered_by' in cleaned_data:
            cleaned_data['registered_by'] = cleaned_data['registered_by'].id

        return cleaned_data


class DepositoryFundElementForms(forms.ModelForm):
    chairman = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Председатель комиссии',
        required=True,
        widget=forms.Select
    )
    vice_chairman = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Зам. председателя комиссии',
        required=True,
        widget=forms.Select
    )
    member_1 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 1',
        required=True,
        widget=forms.Select
    )
    member_2 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 2',
        required=True,
        widget=forms.Select
    )
    member_3 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 3',
        required=True,
        widget=forms.Select
    )
    submitted_by = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Списанные документы сдал(а)',
        required=True,
        widget=forms.Select
    )
    registered_by = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='В книге суммарного учета акт проведен',
        required=True,
        widget=forms.Select
    )

    class Meta:
        model = DepositoryFundElement
        exclude = []

    def clean(self):
        cleaned_data = super().clean()

        if self.instance:
            total_excluded = self.instance.total_excluded
        else:
            total_excluded = 0

        socio_economic_count = cleaned_data.get('socio_economic_count', 0)
        technical_count = cleaned_data.get('technical_count', 0)
        other_count = cleaned_data.get('other_count', 0)
        railway_theme_count = cleaned_data.get('railway_theme_count', 0)

        total_count = socio_economic_count + technical_count + other_count + railway_theme_count

        if total_count > total_excluded:
            raise ValidationError(
                'Сумма полей "Социально-экономическое количество", '
                '"Техническое количество", "Прочее количество" и '
                '"Количество по железнодорожной тематике" не должна превышать общее количество исключенных.'
            )

        if 'chairman' in cleaned_data:
            cleaned_data['chairman'] = cleaned_data['chairman'].id

        if 'vice_chairman' in cleaned_data:
            cleaned_data['vice_chairman'] = cleaned_data['vice_chairman'].id

        if 'member_1' in cleaned_data:
            cleaned_data['member_1'] = cleaned_data['member_1'].id

        if 'member_2' in cleaned_data:
            cleaned_data['member_2'] = cleaned_data['member_2'].id

        if 'member_3' in cleaned_data:
            cleaned_data['member_3'] = cleaned_data['member_3'].id

        if 'submitted_by' in cleaned_data:
            cleaned_data['submitted_by'] = cleaned_data['submitted_by'].id

        if 'registered_by' in cleaned_data:
            cleaned_data['registered_by'] = cleaned_data['registered_by'].id

        return cleaned_data
    

class ReplacementActForm(forms.ModelForm):
    chairman = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Председатель комиссии',
        required=True,
        widget=forms.Select(attrs={'class': 'select2'})
    )
    vice_chairman = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Зам. председателя комиссии',
        required=True,
        widget=forms.Select(attrs={'class': 'select2'})
    )
    member_1 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 1',
        required=True,
        widget=forms.Select(attrs={'class': 'select2'})
    )
    member_2 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 2',
        required=True,
        widget=forms.Select(attrs={'class': 'select2'})
    )
    member_3 = forms.ModelChoiceField(
        queryset=Worker.objects.using('belrw-user-db').all(),
        label='Член комиссии 3',
        required=True,
        widget=forms.Select(attrs={'class': 'select2'})
    )
    submitted_by = forms.IntegerField(required=False, widget=forms.HiddenInput())
    registered_by = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ReplacementAct
        fields = [
            'act_number',
            'act_date',
            'socio_economic_count',
            'technical_count',
            'other_count',
            'railway_theme_count',
            'chairman',
            'vice_chairman',
            'member_1',
            'member_2',
            'member_3',
            'submitted_by',
            'registered_by'
        ]

    def clean(self):
        cleaned_data = super().clean()
        logger.info(f"=== ReplacementActForm clean ===")
        logger.info(f"Cleaned data: {cleaned_data}")
        
        # Убираем проверку total_excluded, так как она не нужна для акта замены
        
        for field in ['chairman', 'vice_chairman', 'member_1', 'member_2', 'member_3']:
            if field in cleaned_data and cleaned_data[field]:
                cleaned_data[field] = cleaned_data[field].id
                
        return cleaned_data