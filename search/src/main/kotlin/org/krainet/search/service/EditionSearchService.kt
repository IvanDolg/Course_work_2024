package org.krainet.search.service

import co.elastic.clients.elasticsearch.ElasticsearchClient
import co.elastic.clients.elasticsearch._types.query_dsl.*
import co.elastic.clients.elasticsearch.core.SearchRequest
import co.elastic.clients.elasticsearch.core.SearchResponse
import co.elastic.clients.util.ObjectBuilder
import org.krainet.search.utils.*
import org.krainet.search.view.edition.EditionIndexView
import org.krainet.search.view.edition.EditionView
import org.krainet.search.view.edition.PaginationView
import org.krainet.search.view.SelectionView
import org.krainet.search.view.edition.basic.BasicFilterView
import org.krainet.search.view.edition.basic.BasicQueryView
import org.krainet.search.view.edition.basic.SearchBasicView
import org.krainet.search.view.edition.extended.ExtendedQueryView
import org.krainet.search.view.edition.extended.FilterExtendedView
import org.krainet.search.view.edition.extended.SearchExtendedView
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.stereotype.Service


@Service
class EditionSearchService {

    private val INDEX = "edition"

    @Autowired
    private lateinit var client: ElasticsearchClient

    fun buildBasicSearch(filter: BasicQueryView): SearchRequest {
         val searchRequest = SearchRequest.of {
             it.index(INDEX)
             addSize(it, filter.pagination)
             addQuery(it, filter.search)
             addFilters(it, filter.filters)
        }

        return searchRequest
    }

    fun buildExtendedSearch(filter: ExtendedQueryView): SearchRequest {
        val searchRequest = SearchRequest.of {
            it.index(INDEX)
            addSize(it, filter.pagination)
            addQuery(it, filter.search)
            addFilters(it, filter.filters)
        }

        return searchRequest
    }

    fun addSize(builder: SearchRequest.Builder, pagination: PaginationView) {
        builder.size(pagination.size)
        builder.from(pagination.size?.let { pagination.page?.times(it) })
    }

    fun addQuery(builder: SearchRequest.Builder, query: SearchBasicView) {
        if (!query.query.isNullOrBlank() && !query.field.isNullOrBlank()) {
            if (query.mode.equals("prefix")) {
                queryWithPrefix(builder, query.query, query.field)
            } else if (query.mode.equals("term")) {
                queryWithTerm(builder, query.query, query.field)
            } else if (query.mode.equals("match_phrase")) {
                queryWithMatchPhrase(builder, query.query, query.field)
            } else {
                queryWithMatch(builder, query.query, query.field)
            }
        }
    }

    fun addQuery(builder: SearchRequest.Builder, query: MutableList<SearchExtendedView>) {
        query.forEach { item ->
            if (!item.query.isNullOrBlank() && !item.field.isNullOrBlank()) {
                queryWithMatch(builder, item.query, item.field)
            }
        }
    }

    fun makeRangeFilter(filters: MutableList<Query>, filter: String, value: Pair<String?, String?>) {
        val fv = if (value.first.isNullOrEmpty()) null else value.first
        val tv = if (value.second.isNullOrEmpty()) null else value.second
        filters.add(
            Query.of { it ->
                it.range(
                    RangeQuery.of {
                        it.field(filter).from(fv).to(tv)
                    }
                )
            }
        )
    }

    fun makeFilters(filters: BasicFilterView): List<Query> {
        val result: MutableList<Query> = mutableListOf()
        makeTermFilter(result, "database", filters.database)
        makeListTermFilter(result, "type", filters.types.map { it.name }.toMutableList())
        makeListTermFilter(result, "subtype", filters.subtypes.map { it.name }.toMutableList())
        makeRangeFilter(result, "date_of_publication", Pair(dateToString(filters.pubDate.pubDateFrom, "yyyy-MM-dd"),
            dateToString(filters.pubDate.pubDateTo, "yyyy-MM-dd")))
        return result
    }

    fun makeFilters(filters: FilterExtendedView): List<Query> {
        val result: MutableList<Query> = mutableListOf()
        makeListTermFilter(result, "database", filters.databases)
        makeListTermFilter(result, "type", filters.types.map { it.name }.toMutableList())
        makeListTermFilter(result, "subtype", filters.subtypes.map { it.name }.toMutableList())
        makeRangeFilter(result, "date_of_publication", Pair(dateToString(filters.pubDate.pubDateFrom, "yyyy-MM-dd"),
            dateToString(filters.pubDate.pubDateTo, "yyyy-MM-dd")))
        return result
    }

    fun addFilters(builder: SearchRequest.Builder, filters: BasicFilterView): ObjectBuilder<SearchRequest>? {
        val f = makeFilters(filters)
        if (f.isNotEmpty()) {
            val boolQuery = BoolQuery.of({ it.must(f) })
            builder.postFilter(Query.of({ it.bool(boolQuery) }))
        }

        return builder
    }

    fun addFilters(builder: SearchRequest.Builder, filters: FilterExtendedView): ObjectBuilder<SearchRequest>? {
        val f = makeFilters(filters)
        if (f.isNotEmpty()) {
            val boolQuery = BoolQuery.of({ it.must(f) })
            builder.postFilter(Query.of({ it.bool(boolQuery) }))
        }

        return builder
    }

    fun createElement(l: EditionIndexView?): EditionView {
        val result = if (l != null) {
            EditionView(l)
        } else {
            EditionView()
        }
        return result
    }

    fun printHits(view: SelectionView<EditionView>, res: SearchResponse<EditionIndexView>) {
        for (l in res.hits().hits()) {
            view.elements.add(createElement(l.source()))
        }
        view.size = res.hits().total()?.value() ?: 0
    }

    fun search(query: Map<String, String>): SelectionView<EditionView> {
        val filter = parseQueryToBasicQueryView(query)
        val result = SelectionView<EditionView>()
        val searchRequest = buildBasicSearch(filter)
        val response = client.search(searchRequest, EditionIndexView::class.java)
        printHits(result, response)
        result.page = filter.pagination.page
        result.pageSize = filter.pagination.size
        return result
    }

    fun extendedSearch(query: Map<String, String>): SelectionView<EditionView> {
        val filter = parseQueryToExtendedQueryView(query)
        val result = SelectionView<EditionView>()
        val searchRequest = buildExtendedSearch(filter)
        val response = client.search(searchRequest, EditionIndexView::class.java)
        printHits(result, response)
        result.page = filter.pagination.page
        result.pageSize = filter.pagination.size
        return result
    }
}