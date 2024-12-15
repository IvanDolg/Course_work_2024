package org.krainet.search.view.edition.extended

import com.fasterxml.jackson.annotation.JsonProperty

class SearchExtendedView() {
    @JsonProperty("query")
    var query: String? = ""

    @JsonProperty("field")
    var field: String? = ""

    constructor(query: String?, field: String?) : this() {
        this.query = query
        this.field = field
    }
}