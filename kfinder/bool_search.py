import logging

from django.db.models import Q, Value, F
from django.db.models.functions import Concat, Coalesce
from django.db import connection
from sqlparse import format as sql_format

from kcatalog.models import Belmarc
from kfinder.fields_enum import FIELDS

logger = logging.getLogger(__name__)


class Operand:
    field = None
    value = None
    is_text_index = False
    delimiter = None

    def __init__(self, field, value, is_text_index, delimiter='='):
        if value.startswith('"'):
            value = value[1:-1]
        self.field = field
        self.value = value
        self.is_text_index = is_text_index
        self.delimiter = delimiter

    def __str__(self):
        return f'{self.field}{self.delimiter}{self.value}'
        
    def __repr__(self):
        return f'Operand({self.field}{self.delimiter}{self.value})'
    

    def devide(self):
        value = self.value
        result = []
        i = 0
        while i < len(value):
            if value[i] == '|' or value[i] == '&':
                result.append(Operand(self.field, value[:i].strip(), self.is_text_index, self.delimiter))
                result.append(value[i])
                value = value[i+1:]
                i = 0
            i += 1
        result.append(Operand(self.field, value.strip(), self.is_text_index, self.delimiter))
        if len(result) == 1:
            return [self]
        else:
            result.insert(0, '(')
            result.append(')')
            return result
        

    def convert_field(self):
        result = []
        for field in FIELDS[self.field]:
            result.append(Operand(field['name'], self.value, self.is_text_index, self.delimiter))
            result.append('|')
        result.pop()
        if len(result) == 1:
            return result
        else:
            result.insert(0, '(')
            result.append(')')
            return result
        


def devide_one(operand: Operand):
    result = []
    index = operand.value.find(' | ')
    if index != -1:
        result.append(Operand(operand.field, operand.value[:index].strip(), operand.is_text_index))
        result.append('|')
        result.extend(devide_one(Operand(operand.field, operand.value[index+3:].strip(), operand.is_text_index)))
    index = operand.value.find(' & ')
    if index != -1:
        result.append(Operand(operand.field, operand.value[:index].strip(), operand.is_text_index))
        result.append('&')
        result.extend(devide_one(Operand(operand.field, operand.value[index+3:].strip(), operand.is_text_index)))
    if len(result) == 0:
        return [operand]
    else:
        return result


def covert_query(query):
    query = query.replace('(', ' ( ').replace(')', ' ) ')
    query = query.replace(' OR ', ' | ').replace(' AND ', ' & ')
    query = query.replace(' or ', ' | ').replace(' and ', ' & ')
    query = query.strip()
    return query


def tokenize_query(query):
    result = []
    current_token = ''
    in_quotes = False

    i = 0
    while i < len(query):
        char = query[i]
        
        # Обработка кавычек
        if char == '"':
            in_quotes = not in_quotes
            current_token += char
        
        # Если встретили пробел
        elif char.isspace():
            # Если мы не в кавычках, то завершаем текущий токен
            if not in_quotes and current_token:
                result.append(current_token)
                current_token = ''
            # Если мы в кавычках, добавляем пробел к текущему токену
            elif in_quotes:
                current_token += char
        
        # Для всех остальных символов
        else:
            current_token += char
        
        i += 1
    
    # Добавляем последний токен, если он есть
    if current_token:
        result.append(current_token)
    
    # Убираем пустые токены
    result = [token for token in result if token.strip()]
    
    logger.info(f'tokens: {result}')
    return result


def check_text_index(field_name_str):
    if field_name_str[0] == 'w':
        return field_name_str[1:], True 
    else:
        return field_name_str, False
    

def convert_tokens(tokens):
    result = []
    delimiters = ["<=", ">=", '=', '<', '>']  # Порядок важен! Сначала проверяем двухсимвольные
    
    for token in tokens:
        if token in ('&', '|', '(', ')'):
            result.append(token)
            continue
            
        # Ищем делимитер в токене
        delimiter = None
        split_index = -1

        for delim in delimiters:
            if delim in token:
                delimiter = delim
                split_index = token.index(delim)
                break
        
        if delimiter is None:
            raise ValueError(f"Не найден делимитер в токене: {token}")
            
        field = token[:split_index]
        value = token[split_index + len(delimiter):]
        
        field_name, is_text_index = check_text_index(field)
        result.append(Operand(field_name, value, is_text_index, delimiter))
    
    return result


def devide_tokens(tokens):
    result = []
    for token in tokens:
        if isinstance(token, Operand):
            result.extend(token.devide())
        else:
            result.append(token)
    logger.info(f'devided tokens: {result}')
    return result

def convert_field_tokens(tokens):
    result = []
    for token in tokens:
        if isinstance(token, Operand):
            result.extend(token.convert_field())
        else:
            result.append(token)
    return result

def convert_code_to_annotations(tokens):
    if isinstance(tokens, str):
        codes = {tokens}
    else:
        codes = set()
        for token in tokens:
            if isinstance(token, Operand):
                codes.add(token.field)
    
    annotations = {}
    for field_name in codes:
        for field_config in FIELDS[field_name]:
            # Если поле одиночное (без конкатенации)
            if len(field_config['fields']) == 1:
                annotations[field_config['name']] = Coalesce(F(field_config['fields'][0]), Value(''))
                continue
                
            # Для множественных полей используем конкатенацию
            concat_args = []
            for field in field_config['fields']:
                concat_args.append(Coalesce(F(field), Value('')))
                concat_args.append(Value(' '))
            
            if concat_args:
                concat_args.pop()
            
            if len(concat_args) == 1:
                annotations[field_config['name']] = concat_args[0]
            else:
                annotations[field_config['name']] = Concat(*concat_args)
    
    return annotations if annotations else {}


def parse_expression(tokens, start):
    current_query = None
    i = start
    
    while i < len(tokens):
        token = tokens[i]
        
        # Обработка открывающей скобки
        if token == '(':
            sub_query, new_i = parse_expression(tokens, i + 1)
            if current_query is None:
                current_query = sub_query
            elif i > 0 and tokens[i-1] == '&':
                current_query = current_query & sub_query
            elif i > 0 and tokens[i-1] == '|':
                current_query = current_query | sub_query
            i = new_i
        
        # Обработка закрывающей скобки
        elif token == ')':
            # Проверяем следующий токен после скобки
            if i + 2 < len(tokens):
                next_op = tokens[i+1]
                if next_op in ('&', '|'):
                    next_token = tokens[i+2]
                    if isinstance(next_token, Operand):
                        field_query = convert_code_to_query(next_token)
                        if next_op == '&':
                            current_query = current_query & field_query
                        else:  # |
                            current_query = current_query | field_query
                        i += 2
            return current_query, i
        
        # Пропускаем логические операторы
        elif token in ('&', '|'):
            i += 1
            continue
        
        # Обработка Operand
        elif isinstance(token, Operand):
            field_query = convert_code_to_query(token)
            
            if current_query is None:
                current_query = field_query
            elif i > 0:
                if tokens[i-1] == '&':
                    current_query = current_query & field_query
                elif tokens[i-1] == '|':
                    current_query = current_query | field_query
        
        i += 1
    
    return current_query, i


def build_query(tokens, annotations):
    # Сначала создаем базовый queryset с аннотациями
    # base_queryset = Belmarc.objects.annotate(**annotations)
    
    # Теперь используем аннотированные поля в фильтрации
    final_query, _ = parse_expression(tokens, 0)
    
    if final_query is None:
        return Q()
    
    # query = base_queryset.filter(final_query)
    # sql = str(query.query)
    # formatted_sql = sql_format(sql, reindent=True, keyword_case='upper')
    # logger.info(f'Generated SQL Query:\n{formatted_sql}')
    
    return final_query


def bool_search(query):
    query = covert_query(query)
    tokens = tokenize_query(query)
    tokens = convert_tokens(tokens)
    annotations = convert_code_to_annotations(tokens)
    tokens = devide_tokens(tokens)
    tokens = convert_field_tokens(tokens)
    final_query = build_query(tokens, annotations)
    return annotations, final_query


def convert_code_to_query(operand: Operand):
    field_lookup = {
        '=': '__icontains',
        '<': '__lt',
        '>': '__gt',
        '<=': '__lte',
        '>=': '__gte'
    }
    
    if operand.value.startswith('"'):
        return Q(**{f'{operand.field}__icontains': operand.value[1:-1]})
    if operand.value[0] == '?':
        return Q(**{f'{operand.field}__iendswith': operand.value[1:]})
    if operand.value[-1] == '?':
        return Q(**{f'{operand.field}__istartswith': operand.value[:-1]})
    
    lookup = field_lookup.get(operand.delimiter)
    if lookup is None:
        raise ValueError(f"Неподдерживаемый делимитер: {operand.delimiter}")
        
    if operand.is_text_index:
        return Q(**{f'{operand.field}__icontains': operand.value})
    else:
        return Q(**{f'{operand.field}{lookup}': operand.value})