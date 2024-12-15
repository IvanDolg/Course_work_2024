package org.krainet.search.utils

import co.elastic.clients.json.JsonData
import org.krainet.search.model.Filter
import org.krainet.search.model.Pagination
import org.krainet.search.model.Range
import org.krainet.search.model.Term

fun parsePagination(query: Map<String, String>): Pagination {
    val page = query["page"]?.toIntOrNull() ?: 0
    val size = query["size"]?.toIntOrNull() ?: 20

    return Pagination(page, size)
}

fun parseTerm(query: Map<String, String>): Term? {
    val termPairs = query.entries
        .firstOrNull { (key, _) -> key.startsWith("term_") }

    return termPairs?.let { (key, value) ->
        val field: String = key.removePrefix("term_")
        val parts = value.split("_", limit = 2)
        val mode = if (parts.size > 1) parts[0] else null
        val termValue = parts.getOrElse(1) { parts[0] }
        Term(field, mode, termValue)
    }
}

fun parseFilters(query: Map<String, String>): MutableList<Filter> {
    return query.entries.filter { (key, _) -> key.startsWith("filter_") }
        .map { (key, value) ->
            val field: String = key.removePrefix("filter_")
            val parts = value.split("_", limit = 2)
            val mode = if (parts.size > 1) parts[0] else null
            val filterValue = parts.getOrElse(1) { parts[0] }
            Filter(field, mode, filterValue.split(",").toMutableList())
        }.toMutableList()
}

fun parseRange(input: MutableList<String>): Range {
    val range = Range()

    input.forEach { item ->
        val regex = Regex("(\\w+)\\(([^)]+)\\)")
        val matchResult = regex.find(item)

        matchResult?.let { result ->
            val (key, value) = result.destructured
            when (key) {
                "gt" -> range.gt = JsonData.of(value)
                "gte" -> range.gte = JsonData.of(value)
                "lt" -> range.lt = JsonData.of(value)
                "lte" -> range.lte = JsonData.of(value)
                "from" -> range.from = value
                "to" -> range.to = value
            }
        }
    }

    return range
}