#!/bin/bash

# Переменные
PERIODICAL_DIR="src/main/resources/seed/periodical"  # Путь к периодическим изданиям с JSON файлами
NON_PERIODICAL_DIR="src/main/resources/seed/non-periodical"  # Путь к периодическим изданиям с JSON файлами
ELASTIC_URL="http://localhost:9200"  # URL Elasticsearch
INDEX_NAME="edition"  # Название индекса в Elasticsearch

# Проверка существования каталогов
if [ ! -d "$PERIODICAL_DIR" ]; then
  echo "Каталог $PERIODICAL_DIR не найден."
  exit 1
fi

if [ ! -d "$NON_PERIODICAL_DIR" ]; then
  echo "Каталог $NON_PERIODICAL_DIR не найден."
  exit 1
fi


# Цикл по всем JSON файлам в каталоге
iteration=1
for FILE in $(ls "$PERIODICAL_DIR"/*.json | sort -t'_' -k2,2n); do
  if [ -f "$FILE" ]; then
    echo "Отправка $FILE в индекс $INDEX_NAME"

    # Отправка запроса на создание документа в Elasticsearch
    curl -X POST "$ELASTIC_URL/$INDEX_NAME/_doc/per$iteration" \
      -H "Content-Type: application/json" \
      -d @"$FILE"

    echo "Файл $FILE отправлен."

    iteration=$((iteration + 1))
  else
    echo "Файлов JSON не найдено в $PERIODICAL_DIR."
  fi
done

iteration=1
for FILE in $(ls "$NON_PERIODICAL_DIR"/*.json | sort -t'_' -k2,2n); do
  if [ -f "$FILE" ]; then
    echo "Отправка $FILE в индекс $INDEX_NAME"

    # Отправка запроса на создание документа в Elasticsearch
    curl -X POST "$ELASTIC_URL/$INDEX_NAME/_doc/nop$iteration" \
      -H "Content-Type: application/json" \
      -d @"$FILE"

    echo "Файл $FILE отправлен."

    iteration=$((iteration + 1))
  else
    echo "Файлов JSON не найдено в $NON_PERIODICAL_DIR."
  fi
done