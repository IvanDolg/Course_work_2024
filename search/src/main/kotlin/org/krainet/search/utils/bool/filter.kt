package org.krainet.search.utils.bool

import co.elastic.clients.elasticsearch._types.query_dsl.Query
import org.krainet.search.utils.*

fun filterFabric(field: String, mode: String, value: String): Query {
    return when(parseMode(field, mode, value)) {
        "prefix" -> prefixFilter(field, value)
        "match" -> matchFilter(field, value)
        "wildcard" -> wildcardFilter(field.substring(1), "*${value}*")
        "range" -> rangeFilter(field, parseRange(convertToRangeValue(mode, value)))
        else -> termFilter(field, value)
    }
}