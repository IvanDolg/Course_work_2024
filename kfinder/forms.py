from django import forms

from kfinder.utils import years

DOCUMENT_TYPES = [
    ('BOOK', 'Книги'),
    ('E_RESOURCE', 'Электронный ресурс'),
    ('MAGAZINES', 'Журналы'),
    ('BROCHURE', 'Брошюры'),
    ('STD', 'НТД'),
    ('NEWSPAPERS', 'Газеты'),
    ('INFORMATION_FLYER', 'Информационные листки'),
    ('STD_CHANGES', 'Изменения и дополнения к НТД'),
]

SEARCH_MODES = [
    ('prefix', 'С начала'),
    ('term', 'Точное с'),
    ('match-phrase', 'Фраза'),
    ('match', 'Все слова'),
]

SEARCH_FIELDS = [
    ('title', 'Заглавие'),
    ('author', 'Автор'),
    ('topic', 'Тема'),
    ('all_fields', 'Все поля'),
]

DATABASE_TYPES = [
    ('database 1', 'database 1'),
    ('DB "Lean manufacturing"', 'БД “Бережливое производство”'),
    ('DB "The history of the Belarusian railway"', 'БД “История белорусской железной дороги”'),
    ('DB "Common Economic Space"', 'БД “Единое экономическое пространство”'),
    ('DB "Conferences, works"', 'БД “Конференции, труды”'),
    ('DB "Best practices. Information sheets"', 'БД “Передовой опыт. Информационные листки”'),
    ('DB "Technic. New technologies"', 'БД “Техника. Новые технологии”'),
]

PAGE_SIZE_CHOICES = [
    (5, '5'),
    (10, '10'),
    (20, '20'),
    (50, '50'),
]


class SearchForm(forms.Form):

    document_type = forms.MultipleChoiceField(
        choices=DOCUMENT_TYPES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Вид документа'
    )

    database = forms.ChoiceField(
        choices=[('', '')] + DATABASE_TYPES,
        required=False,
        label='База данных',
        widget=forms.Select()
    )

    search_query = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={'placeholder': 'Введите запрос'})
    )

    search_mode = forms.ChoiceField(
        choices=SEARCH_MODES,
        widget=forms.RadioSelect,
        required=False,
        label='Режим поиска'
    )

    search_field = forms.ChoiceField(
        choices=SEARCH_FIELDS,
        widget=forms.RadioSelect,
        required=False,
        label='Область поиска'
    )

    pub_date_from = forms.DateField(
        required=False,
        label='Год издания С',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    pub_date_to = forms.DateField(
        required=False,
        label='До',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    page = forms.IntegerField(
        required=False,
        initial=1
    )

    page_size = forms.ChoiceField(
        choices=PAGE_SIZE_CHOICES,
        initial=20,
        required=False,
    )


SEARCH_TYPES = [
    ('title', 'Заглавие'),
    ('author', 'Автор'),
    ('series_title', 'Название серии'),
    ('year', 'Год издания')
]


class ExtendedSearchForm(forms.Form):
    title = forms.CharField(
        required=False,
        label="Название"
    )

    author = forms.CharField(
        required=False,
        label="Автор"
    )

    series_title = forms.CharField(
        required=False,
        label="Название серии"
    )

    year_from = forms.ChoiceField(
        choices=[(str(year), str(year)) for year in years()],
        required=False,
        label="Год с"
    )

    year_to = forms.ChoiceField(
        choices=[(str(year), str(year)) for year in years()],
        required=False,
        label="Год по"
    )

    document_type = forms.MultipleChoiceField(
        choices=DOCUMENT_TYPES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Вид документа'
    )

    databases = forms.MultipleChoiceField(
        choices=DATABASE_TYPES,
        required=False,
        label='База данных',
        widget=forms.Select()
    )

    topics = forms.MultipleChoiceField(
        required=False,
        label='Тематика',
        widget=forms.Select()
    )

    page = forms.IntegerField(
        required=False,
        initial=1
    )

    page_size = forms.ChoiceField(
        choices=PAGE_SIZE_CHOICES,
        initial=20,
        required=False,
    )

    def clean_databases(self):
        databases = []
        for key, value in self.data.items():
            if key.startswith('database_') and value:
                databases.append(value)

        return databases

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['databases'] = self.clean_databases()
        return cleaned_data

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['databases'].widget.attrs['class'] = 'database-field'

