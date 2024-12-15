import datetime
import logging
import json

from django.db.models import Q
from dateutil.relativedelta import relativedelta
from django import template
from django.http import HttpResponse
from django.template.defaultfilters import register
from kcatalog.models import Belmarc, Chapter
from kfinder.bool_search import bool_search, build_query, convert_code_to_annotations, tokenize_query
from kfinder.document_generator import generate_bulletin
from kfinder.forms import DOCUMENT_TYPES

from django.core.paginator import Paginator
from django.shortcuts import render

from kuser.models import Reader, Worker
from .forms import SearchForm, DATABASE_TYPES
from .forms import ExtendedSearchForm
import requests

from .utils import convert_year, months, years

logger = logging.getLogger(__name__)

@register.filter
def readable_subtype(value):
    subtype_dict = dict(DOCUMENT_TYPES)
    return subtype_dict.get(value, value)

def periodical(request, id):
    pass
    # if request.method == 'GET':
    #     edition =

def non_periodical(request, id):
    pass
    # if request.method == 'GET':


def basic_search_view(request):
    if request.method == 'GET':
        page_number = request.GET.get('page', 1)
        form = SearchForm(request.GET or None, initial={'page': page_number})

        form.fields['document_type'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['database'].widget.attrs.update({'class': 'form-control'})
        form.fields['search_query'].widget.attrs.update({'class': 'form-control'})
        form.fields['search_mode'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['search_field'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['pub_date_from'].widget.attrs.update({'class': 'form-control'})
        form.fields['pub_date_to'].widget.attrs.update({'class': 'form-control'})
        form.fields['page'].widget.attrs.update({'class': ''})

        results = None
        total_pages = None
        page_number = request.GET.get('page', 1)
        if form.is_valid():
            document_type = form.cleaned_data.get('document_type') or []
            database = form.cleaned_data.get('database') or ''
            search_query = form.cleaned_data.get('search_query') or ''
            search_mode = form.cleaned_data.get('search_mode') or ''
            search_field = form.cleaned_data.get('search_field') or ''
            pub_date_from = form.cleaned_data.get('pub_date_from') or ''
            pub_date_to = form.cleaned_data.get('pub_date_to') or ''
            page = form.cleaned_data.get('page') or 1
            page_size = form.cleaned_data.get('page_size') or 20

            url = (f'http://belrw-search:8080/public/search/sku/search'
                   f'?filter_is_published=match-phrase_true'
                   f'&filter_subtype=terms_{",".join(document_type)}'
                   f'&filter_database=term_{database.replace(" ", "+")}'
                   f'&term_{search_field}={search_mode}_{search_query}'
                   f'&filter_date_of_publication=range_from({pub_date_from}),to({pub_date_to})'
                   f'&size={page_size}'  
                   f'&page={page - 1}')

            response = requests.get(url=url)

            if response.status_code == 200:
                response_data = response.json()
                results = convert_year(response_data.get('elements', []))
                # Применяем функцию readable_subtype к каждому результату
                for result in results:
                    result['readable_subtype'] = readable_subtype(result['subtype'])
                total_results = response_data.get('size', 0)

                total_pages = (total_results + int(page_size) - 1) // int(page_size)
            else:
                results = []

        page_numbers = list(range(1, total_pages + 1)) if total_pages is not None else []
        selected_document_types = request.GET.getlist('document_type')
        return render(request, 'search_basic.html', {
            'form': form,
            'results': results,
            'total_pages': total_pages if total_pages is not None else 0,
            'current_page': int(page_number),
            'page_numbers': page_numbers,
            'selected_document_types': selected_document_types,
        })


def extended_search_view(request):
    if request.method == 'GET':
        page_number = request.GET.get('page', 1)
        results = None
        total_pages = None
        topics = []
        form = ExtendedSearchForm(request.GET or None, initial={'page': page_number})
        if not form.is_valid():
            logger.error(f"Ошибки формы: {form.errors}")
        page_number = request.GET.get('page', 1)
        if form.is_valid():
            document_type = form.cleaned_data.get('document_type') or []

            databases = [value for key, value in request.GET.items() if key.startswith('database_')] or ''
            topics = request.GET.getlist("selected_topics")
            title = form.cleaned_data.get('title') or ''
            author = form.cleaned_data.get('author') or ''
            series_title = form.cleaned_data.get('series_title') or ''
            year_from = form.cleaned_data.get('year_from') or ''
            year_to = form.cleaned_data.get('year_to') or ''
            page = form.cleaned_data.get('page') or 1
            page_size = form.cleaned_data.get('page_size', 20) or 20

            date_filter = ""
            if year_from:
                date_filter += f'from({year_from}-01-01),'
            if year_to:
                date_filter += f'to({year_to}-12-31),'
            date_filter = date_filter.rstrip(',')

            url = (
                f'http://belrw-search:8080/public/search/sku/search'
                f'?filter_subtype=terms_{",".join(document_type)}'
                f'&filter_database=terms_{",".join([db.replace(" ", "+") for db in databases])}'
                f'&filter_subject=terms_{",".join(topics)}'
                f'&filter_title=match_{title}'
                f'&filter_author=match_{author}'
                f'&filter_series_title=match_{series_title}'
                f'&filter_date_of_publication=range_{date_filter}'
                f'&size={page_size}'
                f'&page={page - 1}'
            )

            logger.debug(url)

            response = requests.get(url=url)

            if response.status_code == 200:
                response_data = response.json()
                results = convert_year(response_data.get('elements', []))
                total_results = response_data.get('size', 0)
                for result in results:
                    result['readable_subtype'] = readable_subtype(result['subtype'])

                total_pages = (total_results + int(page_size) - 1) // int(page_size)
            else:
                results = []

        page_numbers = list(range(1, total_pages + 1)) if total_pages is not None else []
        selected_document_types = request.GET.getlist('document_type')

        entity = {
            'form': form,
            'databases': json.dumps([('', 'Выберите базу даных')] + DATABASE_TYPES),
            'years': years,
            'results': results,
            'total_pages': total_pages if total_pages is not None else 0,
            'current_page': int(page_number),
            'page_numbers': page_numbers,
            'selected_document_types': selected_document_types,
            'selected_databases': [value for key, value in request.GET.items() if key.startswith('database_')],
            'selected_title': request.GET.get('title', ''),
            'selected_author': request.GET.get('author', ''),
            'selected_series_title': request.GET.get('series_title', ''),
            'selected_year_from': request.GET.get('year_from', ''),
            'selected_year_to': request.GET.get('year_to', ''),
            'selected_topics': topics if topics else [],  
        }

        return render(request, 'extended_search.html', entity)

from django.contrib.auth.decorators import login_required

@login_required
def topic_select(request):
    topics = Belmarc.objects.values_list('topical_subject__topic', flat=True).distinct().order_by('topical_subject__topic')
    topics = [topic for topic in topics if topic]

    selected_topics = request.GET.get('selected_topics', '').split(',')
    selected_topics = [topic.strip() for topic in selected_topics if topic.strip()]

    context = {
        'topics': topics,
        'selected_topics': selected_topics,
    }
    return render(request, 'topic_select.html', context)

def boolean_search_view(request):
    if request.method == 'GET':
        search_query = request.GET.get('query', '')
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        
        results = None
        total_pages = None
        
        if search_query:
            results = []
            annotations, final_query = bool_search(search_query)
            elements = Belmarc.objects.annotate(**annotations).filter(final_query)            
            for element in elements:
                temp = {
                    'id': element.id,
                    'readable_subtype': element.edition().edition_subtype,
                    'title': element.title_and_statement_of_responsibility.title,
                    'year': element.edition().year
                }
                results.append(temp)
            total_results = len(results)
            total_pages = (total_results + int(page_size) - 1) // int(page_size)

        page_numbers = list(range(1, total_pages + 1)) if total_pages is not None else []
        
        return render(request, 'search_boolean.html', {
            'search_query': search_query,
            'results': results,
            'total_pages': total_pages if total_pages is not None else 0,
            'current_page': int(page_number),
            'page_numbers': page_numbers,
        })


def new_releases_search(request):
    if request.method == 'GET':

        current_date = datetime.date.today()
        date_last_month = current_date - relativedelta(months=1)

        logger.debug(date_last_month)
        skus = Belmarc.objects.filter(created_at__gte=date_last_month, is_published=True)
        results = []
        for sku in skus:
            edition = sku.edition()
            if edition:
                temp = {
                    'id': sku.id,
                    'readable_subtype': edition.get_edition_subtype_display(),
                    'title': edition.title,
                    'year': edition.year
                }
                results.append(temp)

        return render(request, 'new_sku.html', {
            'results': results,
        })

def chapter(request):
    chapters = Chapter.objects.all()
    available_years = years()
    available_months = months()

    if request.method == 'GET':
        query = request.GET.get('query', '')
        year = request.GET.get('year', '2023')
        month = request.GET.get('month', 'Январь')

        if query:

            results = []
            search_query = Chapter.objects.filter(id=query).first()
            annotations, final_query = bool_search(search_query.query)
            results = Belmarc.objects.annotate(**annotations).filter(final_query)     
                    
            reader = Reader.objects.filter(user=request.user).first()
            worker = Worker.objects.filter(user=request.user).first()
            library = reader.library if reader else worker.library if worker else ''
            # Генерируем документ
            doc = generate_bulletin(results, library, search_query.name)
            
            # Создаем HTTP-ответ с файлом
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename=bulletin_{year}_{month}.docx'
            
            # Сохраняем документ в response
            doc.save(response)
            
            return response

    return render(request, 'chapter.html', {
        'chapters': chapters,
        'years': available_years,
        'months': available_months,
        'selected_year': year,
        'selected_month': month,
    })
