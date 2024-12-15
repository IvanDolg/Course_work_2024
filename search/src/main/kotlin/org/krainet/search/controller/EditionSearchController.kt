package org.krainet.search.controller

import org.krainet.search.service.EditionSearchService
import org.krainet.search.view.SelectionView
import org.krainet.search.view.edition.EditionView
import org.krainet.search.view.edition.basic.BasicQueryView
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/public/search/edition")
class EditionSearchController {

    @Autowired
    private lateinit var service: EditionSearchService

    /**
     * page           - result list page number
     * size           - result list page size
     * orderBy        - result list sort field names +/- sort direction separated _
     * term           - result list search term
     * filter_{name}  - result list search filter separated _
     * all_{name}     - result list search filter separated _
     */
    @RequestMapping("/basic")
    fun basicSearch(@RequestParam query: Map<String, String>): ResponseEntity<SelectionView<EditionView>> {
        val result: SelectionView<EditionView> = service.search(query)
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }

    @RequestMapping("/search")
    fun search(@RequestParam query: Map<String, String>): ResponseEntity<SelectionView<EditionView>> {
        val result: SelectionView<EditionView> = service.search(query)
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }

    @RequestMapping("/extended")
    fun extendedSearch(@RequestParam query: Map<String, String>): ResponseEntity<SelectionView<EditionView>> {
        val result: SelectionView<EditionView> = service.extendedSearch(query)
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }
}