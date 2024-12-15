package org.krainet.search.view.edition.extended

import com.fasterxml.jackson.annotation.JsonProperty
import org.krainet.search.view.edition.PaginationView

class ExtendedQueryView {
    @JsonProperty("pagination")
    var pagination: PaginationView = PaginationView(0, 10)

    @JsonProperty("search")
    var search: MutableList<SearchExtendedView> = mutableListOf()

    @JsonProperty("filters")
    var filters: FilterExtendedView = FilterExtendedView()
}