package org.krainet.search.controller

import org.krainet.search.service.SkuIndexService
import org.krainet.search.view.AddView
import org.krainet.search.view.sku.SkuView
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/public/search/sku")
class SkuIndexController {

    @Autowired
    private lateinit var service: SkuIndexService

    @RequestMapping("/add/{id}")
    fun add(@PathVariable id: String, @RequestBody sku: SkuView): ResponseEntity<AddView> {
        val result = service.add(id, sku)
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }

    @RequestMapping("/delete/{id}")
    fun delete(@PathVariable id: String): ResponseEntity<AddView> {
        val result = service.delete(id)
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }

    @RequestMapping("/index/{id}")
    fun index(@PathVariable id: String, @RequestBody sku: SkuView): ResponseEntity<AddView> {
        val result = service.index(id, sku)
        return ResponseEntity.status(HttpStatus.OK).body(result)
    }
}