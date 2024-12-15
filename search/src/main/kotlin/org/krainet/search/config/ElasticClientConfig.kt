package org.krainet.search.config

import co.elastic.clients.elasticsearch.ElasticsearchClient
import co.elastic.clients.json.jackson.JacksonJsonpMapper
import co.elastic.clients.transport.ElasticsearchTransport
import co.elastic.clients.transport.rest_client.RestClientTransport
import org.apache.http.HttpHost
import org.elasticsearch.client.RestClient
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.core.env.Environment
import org.springframework.core.env.get
import org.springframework.data.elasticsearch.config.ElasticsearchConfigurationSupport
import org.springframework.stereotype.Service

@Configuration
@Service
class ElasticClientConfig: ElasticsearchConfigurationSupport() {

    @Autowired
    private lateinit var environment: Environment

    @Bean
    fun elasticsearchClient(): ElasticsearchClient {
        val es = environment.get("krainet.elastic.host") + ":" + environment.get("krainet.elastic.port")
        val restClient = RestClient.builder(HttpHost.create(es)).build()
        val transport : ElasticsearchTransport = RestClientTransport(restClient, JacksonJsonpMapper())
        return ElasticsearchClient(transport)
    }
}