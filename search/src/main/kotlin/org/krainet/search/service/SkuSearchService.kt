package org.krainet.search.service

import SkuIndexView
import co.elastic.clients.elasticsearch.ElasticsearchClient
import co.elastic.clients.elasticsearch._types.query_dsl.*
import co.elastic.clients.elasticsearch.core.SearchRequest
import co.elastic.clients.elasticsearch.core.SearchResponse
import co.elastic.clients.util.ObjectBuilder
import com.google.gson.GsonBuilder
import org.krainet.search.model.Filter
import org.krainet.search.model.Pagination
import org.krainet.search.model.SearchQuery
import org.krainet.search.model.Term
import org.krainet.search.utils.*
import org.krainet.search.view.SelectionView
import org.krainet.search.view.sku.SkuView
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.stereotype.Service

@Service
class SkuSearchService {

    private val INDEX = "sku"

    @Autowired
    private lateinit var client: ElasticsearchClient

    fun buildBasicSearch(query: SearchQuery): SearchRequest {
        return SearchRequest.of {
            it.index(INDEX)
            addSize(it, query.pagination)
            addQuery(it, query.term)
            addFilters(it, query.filters)
        }
    }

    fun addSize(builder: SearchRequest.Builder, pagination: Pagination) {
        builder.size(pagination.size)
        builder.from(pagination.size * pagination.page)
    }

    fun addQuery(builder: SearchRequest.Builder, term: Term?) {
        term?.let { queryFabric(builder, it) }
    }

    fun makeFilters(filters: MutableList<Filter>): List<Query> {
        val result: MutableList<Query> = mutableListOf()
        filters.forEach{ filter -> makeFilterFabric(result, filter) }
        return result
    }

    fun addFilters(builder: SearchRequest.Builder, filters: MutableList<Filter>): ObjectBuilder<SearchRequest>? {
        val f = makeFilters(filters)
        if (f.isNotEmpty()) {
            val boolQuery = BoolQuery.of { it.must(f) }
            builder.postFilter(Query.of { it.bool(boolQuery) })
        }

        return builder
    }

    fun createElement(l: SkuIndexView?): SkuView {
        return SkuView(l ?: SkuIndexView())
    }

    fun printHits(view: SelectionView<SkuView>, res: SearchResponse<SkuIndexView>) {
        for (l in res.hits().hits()) {
            view.elements.add(createElement(l.source()))
        }
        view.size = res.hits().total()?.value() ?: 0
    }

    fun search(query: SearchQuery): SelectionView<SkuView> {
        val result = SelectionView<SkuView>()
        val searchRequest = buildBasicSearch(query)
        val gson = GsonBuilder().setPrettyPrinting().create()
        println(gson.toJson(searchRequest))
        val response = client.search(searchRequest, SkuIndexView::class.java)
        printHits(result, response)
        result.page = query.pagination.page
        result.pageSize = query.pagination.size
        return result
    }
}