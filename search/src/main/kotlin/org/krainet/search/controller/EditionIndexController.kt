package org.krainet.search.controller

import org.krainet.search.service.EditionIndexService
import org.krainet.search.view.AddView
import org.krainet.search.view.edition.EditionView
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/public/search/edition")
class EditionIndexController {

    @Autowired
    private lateinit var service: EditionIndexService

    @RequestMapping("/add/{id}")
    fun add(@PathVariable id: String, @RequestBody element: EditionView): ResponseEntity<AddView> {
        val result = service.add(id, element)
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }

    @RequestMapping("/delete/{id}")
    fun delete(@PathVariable id: String): ResponseEntity<AddView> {
        val result = service.delete(id)
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }

    @RequestMapping("/index/{id}")
    fun index(@PathVariable id: String, @RequestBody edition: EditionView): ResponseEntity<AddView> {
        val result = service.index(id, edition)
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }

}