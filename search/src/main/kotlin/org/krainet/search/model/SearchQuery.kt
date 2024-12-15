package org.krainet.search.model

import org.krainet.search.utils.parseFilters
import org.krainet.search.utils.parsePagination
import org.krainet.search.utils.parseTerm

class SearchQuery(
    val term: Term? = null,
    val filters: MutableList<Filter> = mutableListOf(),
    val pagination: Pagination = Pagination(0, 20)
) {
    companion object {
        fun defaultParser(query: Map<String, String>): SearchQuery {
            val obj = SearchQuery(term = parseTerm(query),
                filters = parseFilters(query),
                pagination = parsePagination(query)
            )
            return obj
        }
    }
}