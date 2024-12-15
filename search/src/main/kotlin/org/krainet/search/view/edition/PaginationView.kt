package org.krainet.search.view.edition

import com.fasterxml.jackson.annotation.JsonProperty
import lombok.AllArgsConstructor
import lombok.NoArgsConstructor
import lombok.ToString

class PaginationView(page: Int, size: Int) {

    @JsonProperty("page")
    var page: Int? = page

    @JsonProperty("size")
    var size: Int? = size

    override fun toString(): String {
        return "page=${page}, size=${size}"
    }
}