package org.krainet.search.view.edition.basic

import com.fasterxml.jackson.annotation.JsonProperty
import org.krainet.search.view.edition.PaginationView

class BasicQueryView {

    @JsonProperty("pagination")
    var pagination: PaginationView = PaginationView(0, 10)

    @JsonProperty("search")
    var search: SearchBasicView = SearchBasicView()

    @JsonProperty("filters")
    var filters: BasicFilterView = BasicFilterView()

    @JsonProperty("nofasets")
    var nofasets: String? = "1"

    override fun toString(): String {
        return "pagination=(${pagination.toString()}), filters=${filters.toString()}, " +
                "search=(${search.toString()}), nofasets=${nofasets}"
    }
}