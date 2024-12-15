# Сервис для работы с Elasticsearch

## 1. Запуск сервиса и Elasticsearch

(Запуск происходит относительно пути README.md)

Билд проекта:
```shell
mvn package
```
Запуск контейнеров:
```shell
docker compose -f ../docker-compose.yml up belrw-elastic belrw-search -d
```
## 2. Инициализация Elasticsearch

Выполнить этот запрос для создания индекса:
```shell
curl -X PUT "http://localhost:9200/edition" -H "Content-Type: application/json" -d @edition-index.json
```
Выполнить этот скрипт для заполнения Elasticsearch тестовыми данными:
```shell
./init_index.sh
```

## 3. Параметры запроса:

| Параметр      | Описание           | Пример             | Особенности                                         |
|:--------------|:-------------------|:-------------------|:----------------------------------------------------|
| size          | размер страницы    | 10                 |                                                     |
| page          | номер страницы     | 0                  |                                                     |
| types         | тип наименования   | MAGAZINES,BOOK,STD | указывать список через ','                          |
| database      | база данных        | database+1         | заменить пробелы на '+'                             |
| pub_date_from | дата публикации с  | 2022-01-01         | формат 'yyyy-MM-dd'                                 |
| pub_date_to   | дата публикации по | 2024-11-21         | формат 'yyyy-MM-dd'                                 |
| query         | фраза для поиска   | Elasticsearch      |                                                     |
| mode          | режим поиска       | match_phrase       | принимает 'prefix', 'term', 'match_phrase', 'match' |
| field         | поле для поиска    | title              |                                                     |