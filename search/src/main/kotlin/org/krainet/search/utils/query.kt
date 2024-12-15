package org.krainet.search.utils

import co.elastic.clients.elasticsearch._types.query_dsl.*
import co.elastic.clients.elasticsearch.core.SearchRequest
import org.krainet.search.model.Term

/**
 * Выполняет поиск с использованием префикса в Elasticsearch.
 *
 * @param builder Построитель запроса SearchRequest.
 * @param query Строка запроса для поиска.
 * @param field Поле, по которому выполняется поиск.
 */
fun queryWithPrefix(builder: SearchRequest.Builder, query: String?, field: String?) {
    val searchWord = "*${query?.lowercase()}*"
    val queryCategories = Query.of { it.prefix(PrefixQuery.of { it.field(field).value(searchWord) }) }
    val boolQuery = BoolQuery.of {
        it.should(queryCategories)
    }
    builder.query(Query.of { it.bool(boolQuery) })
}

/**
 * Выполняет поиск с использованием точного совпадения термина в Elasticsearch.
 *
 * @param builder Построитель запроса SearchRequest.
 * @param query Строка запроса для поиска.
 * @param field Поле, по которому выполняется поиск.
 */
fun queryWithTerm(builder: SearchRequest.Builder, query: String?, field: String?) {
    val queryCategories = Query.of { it.term(TermQuery.of { it.field(field).value(query) }) }
    val boolQuery = BoolQuery.of {
        it.should(queryCategories)
    }
    builder.query(Query.of { it.bool(boolQuery) })
}

/**
 * Выполняет поиск с использованием точного совпадения фразы в Elasticsearch.
 *
 * @param builder Построитель запроса SearchRequest.
 * @param query Строка запроса для поиска.
 * @param field Поле, по которому выполняется поиск.
 */
fun queryWithMatchPhrase(builder: SearchRequest.Builder, query: String?, field: String?) {
    val queryCategories = Query.of { it.matchPhrase(MatchPhraseQuery.of { it.field(field).query(query) }) }
    val boolQuery = BoolQuery.of {
        it.should(queryCategories)
    }
    builder.query(Query.of { it.bool(boolQuery) })
}

/**
 * Выполняет поиск с использованием частичного совпадения в Elasticsearch.
 *
 * @param builder Построитель запроса SearchRequest.
 * @param query Строка запроса для поиска.
 * @param field Поле, по которому выполняется поиск.
 */
fun queryWithMatch(builder: SearchRequest.Builder, query: String?, field: String?) {
    val searchWord = "*${query?.lowercase()}*"
    val queryCategories = Query.of { it.match(MatchQuery.of { it.field(field).query(searchWord) }) }
    val boolQuery = BoolQuery.of {
        it.should(queryCategories)
    }
    builder.query(Query.of { it.bool(boolQuery) })
}

fun queryFabric(builder: SearchRequest.Builder, term: Term) {
    if (term.value.isEmpty()) return
    when(term.mode) {
        "prefix" -> queryWithPrefix(builder, term.value, term.field)
        "terms" -> queryWithTerm(builder, term.value, term.field)
        "match-phrase" -> queryWithMatchPhrase(builder, term.value, term.field)
        "match" -> queryWithMatch(builder, term.value, term.field)
        else -> queryWithMatch(builder, term.value, term.field)
    }
}