package org.krainet.search.config

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.http.HttpHeaders
import org.springframework.http.HttpMethod
import org.springframework.http.HttpStatus
import org.springframework.http.server.reactive.ServerHttpRequest
import org.springframework.http.server.reactive.ServerHttpResponse
import org.springframework.web.cors.reactive.CorsUtils
import org.springframework.web.server.ServerWebExchange
import org.springframework.web.server.WebFilter
import org.springframework.web.server.WebFilterChain
import reactor.core.publisher.Mono

@Configuration
class CorsConfiguration {

    private val ALLOWED_HEADERS = "x-requested-with, authorization, Content-Type, Authorization, credential, X-XSRF-TOKEN"
    private val ALLOWED_METHODS = "GET, PUT, POST, DELETE, OPTIONS"
    private val ALLOWED_ORIGIN = "*"
    private val MAX_AGE = "3600"

    @Bean
    fun corsFilter(): WebFilter? {
        return WebFilter { ctx: ServerWebExchange, chain: WebFilterChain ->
            val request: ServerHttpRequest = ctx.request
            if (CorsUtils.isCorsRequest(request)) {
                val response: ServerHttpResponse = ctx.response
                val headers: HttpHeaders = response.getHeaders()
                headers.add("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
                headers.add("Access-Control-Allow-Methods", ALLOWED_METHODS)
                headers.add("Access-Control-Max-Age", MAX_AGE)
                headers.add("Access-Control-Allow-Headers", ALLOWED_HEADERS)
                if (request.getMethod() === HttpMethod.OPTIONS) {
                    response.setStatusCode(HttpStatus.OK)
                    return@WebFilter Mono.empty<Void>()
                }
            }
            chain.filter(ctx)
        }
    }
}