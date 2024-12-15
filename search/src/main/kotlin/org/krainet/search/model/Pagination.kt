package org.krainet.search.model

import com.fasterxml.jackson.annotation.JsonProperty

class Pagination() {

    var page: Int = 0
    var size: Int = 20

    constructor(page: Int, size: Int): this() {
        this.page = page
        this.size = size
    }

    override fun toString(): String {
        return "page=${page}, size=${size}"
    }
}