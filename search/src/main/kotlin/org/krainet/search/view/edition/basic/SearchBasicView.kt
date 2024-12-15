package org.krainet.search.view.edition.basic

import com.fasterxml.jackson.annotation.JsonProperty
import lombok.ToString

class SearchBasicView {
    @JsonProperty("query")
    var query: String? = ""

    @JsonProperty("mode")
    var mode: String? = ""

    @JsonProperty("field")
    var field: String? = ""

    override fun toString(): String {
        return "query=${query}, mode=${mode}, field=${field}"
    }
}