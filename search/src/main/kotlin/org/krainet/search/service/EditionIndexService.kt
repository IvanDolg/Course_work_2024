package org.krainet.search.service

import co.elastic.clients.elasticsearch.ElasticsearchClient
import co.elastic.clients.elasticsearch.core.DeleteRequest
import co.elastic.clients.elasticsearch.core.IndexRequest
import co.elastic.clients.elasticsearch.core.IndexResponse
import io.micrometer.core.annotation.Timed
import org.springframework.beans.factory.annotation.Autowired
import org.krainet.search.getMyLogger
import org.krainet.search.view.AddView
import org.krainet.search.view.edition.EditionIndexView
import org.krainet.search.view.edition.EditionView
import org.springframework.stereotype.Service

@Service
@Timed
class EditionIndexService {

    private val INDEX = "edition"

    @Autowired
    private lateinit var client: ElasticsearchClient

    private val logger = getMyLogger<EditionIndexService>()

    fun add(id: String, element: EditionIndexView): AddView {
        val result = AddView()

        val request = IndexRequest.of { builer: IndexRequest.Builder<EditionIndexView> ->
            builer
                .index(INDEX)
                .id(id)
                .document(element)
        }

        val response: IndexResponse = client.index(request)
        result.index = response.index()
        result.version = response.version()
        return result
    }

    fun add(id: String, element: EditionView): AddView {
        val edition = EditionIndexView(element)
        val result = add(id, edition)

        return result
    }

    fun delete(id: String): AddView {
        val result = AddView()
        val request = DeleteRequest.of { builder: DeleteRequest.Builder ->
            builder
                .index(INDEX)
                .id(id)
        }
        val response = client.delete(request)
        result.index = response.index()
        result.version = response.version()
        return result
    }

    fun index(id: String, edition: EditionView): AddView {
        logger.info("Index")

        val element = EditionIndexView(edition)
        val result = add(id, element)

        return result
    }
}