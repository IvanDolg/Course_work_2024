package org.krainet.search.service.bool

import SkuIndexView
import co.elastic.clients.elasticsearch.ElasticsearchClient
import co.elastic.clients.elasticsearch.core.SearchRequest
import co.elastic.clients.elasticsearch.core.SearchResponse
import co.elastic.clients.util.ObjectBuilder
import com.google.gson.GsonBuilder
import org.krainet.search.model.Pagination
import org.krainet.search.utils.parsePagination
import org.krainet.search.utils.bool.parseQuery
import org.krainet.search.view.SelectionView
import org.krainet.search.view.sku.SkuView
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.stereotype.Service

@Service
class SkuBoolSearchService {

    private val INDEX = "sku"

    @Autowired
    private lateinit var client: ElasticsearchClient

    fun buildSearch(query: Map<String, String>): SearchRequest {
        return SearchRequest.of {
            it.index(INDEX)
            addSize(it, parsePagination(query))
            addBoolFilters(it, query)
        }
    }

    fun addSize(builder: SearchRequest.Builder, pagination: Pagination) {
        builder.size(pagination.size)
        builder.from(pagination.size * pagination.page)
    }

    fun addBoolFilters(builder: SearchRequest.Builder, query: Map<String, String>): ObjectBuilder<SearchRequest>? {

        builder.postFilter(query["query"]?.let { parseQuery(it) })

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

    fun search(query: Map<String, String>): SelectionView<SkuView> {
        val result = SelectionView<SkuView>()
        val searchRequest = buildSearch(query)
        val gson = GsonBuilder().setPrettyPrinting().create()
        println(gson.toJson(searchRequest))
        val response = client.search(searchRequest, SkuIndexView::class.java)
        printHits(result, response)
        result.page = query["page"]?.toInt()
        result.pageSize = query["size"]?.toInt()
        return result
    }
}