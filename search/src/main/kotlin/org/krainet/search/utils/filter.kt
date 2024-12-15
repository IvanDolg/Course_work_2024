package org.krainet.search.utils

import co.elastic.clients.elasticsearch._types.FieldValue
import co.elastic.clients.elasticsearch._types.query_dsl.*
import org.krainet.search.model.Filter
import org.krainet.search.model.Range

fun termFilter(filter: String, value: String): Query {
    return Query.of { it -> it.term(TermQuery.of { it.field(filter).value(value) }) }
}

fun wildcardFilter(filter: String, value: String): Query {
    return Query.of { it -> it.wildcard(WildcardQuery.of { it.field(filter).value(value) }) }
}

fun matchFilter(filter: String, value: String): Query {
    return Query.of { it -> it.match(MatchQuery.of { it.field(filter).query(value) }) }
}

fun prefixFilter(filter: String, value: String): Query {
    return Query.of { it -> it.prefix(PrefixQuery.of { it.field(filter).value(value.dropLast(1)) }) }
}

fun rangeFilter(filter: String, range: Range): Query {
    return Query.of { it ->
        it.range(
            RangeQuery.of {
                it.field(filter)
                    .gt(range.gt)
                    .gte(range.gte)
                    .lt(range.lt)
                    .lte(range.lte)
                    .from(range.from)
                    .to(range.to)
            }
        )
    }
}

fun makeListTermFilter(filters: MutableList<Query>, filter: String, values: MutableList<String>) {
    if (values.any { it.isNotBlank() }) {
        val terms = TermsQueryField.Builder()
            .value(values.stream().map(FieldValue::of).toList())
            .build()

        filters.add(Query.of { it ->
            it.terms(
                TermsQuery.of {
                    it.field(filter)
                    it.terms(terms)
                }
            )
        })
    }
}

fun makeTermFilter(filters: MutableList<Query>, filter: String, value: String?) {
    if (!value.isNullOrEmpty()) {
        filters.add(termFilter(filter, value))
    }
}

fun makeRangeFilter(filters: MutableList<Query>, filter: String, range: Range) {
    filters.add(rangeFilter(filter, range))
}

fun makeFilterFabric(filters: MutableList<Query>, filter: Filter) {
    when(filter.mode) {
        "term" -> makeTermFilter(filters, filter.field, filter.value[0])
        "terms" -> makeListTermFilter(filters, filter.field, filter.value)
        "range" -> makeRangeFilter(filters, filter.field, parseRange(filter.value))
        else -> makeListTermFilter(filters, filter.field, filter.value)
    }
}