package org.krainet.search.controller

import org.krainet.search.model.SearchQuery
import org.krainet.search.service.bool.SkuBoolSearchService
import org.krainet.search.service.SkuSearchService
import org.krainet.search.view.SelectionView
import org.krainet.search.view.sku.SkuView
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/public/search/sku")
class SkuSearchController {

    @Autowired
    private lateinit var service: SkuSearchService

    @Autowired
    private lateinit var boolService: SkuBoolSearchService

    @RequestMapping("/search")
    fun search(@RequestParam query: Map<String, String>): ResponseEntity<SelectionView<SkuView>> {
        val result: SelectionView<SkuView> = service.search(SearchQuery.defaultParser(query))
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }

    @RequestMapping("/bool")
    fun boolSearch(@RequestParam query: Map<String, String>): ResponseEntity<SelectionView<SkuView>> {
        val result: SelectionView<SkuView> = boolService.search(query)
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }
}