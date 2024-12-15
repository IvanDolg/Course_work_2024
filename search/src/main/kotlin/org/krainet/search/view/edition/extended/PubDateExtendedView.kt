package org.krainet.search.view.edition.extended

import com.fasterxml.jackson.annotation.JsonProperty
import java.util.*

class PubDateExtendedView {
    @JsonProperty("pub_year_from")
    var pubYearFrom: Int? = null

    @JsonProperty("pub_year_to")
    var pubYearTo: Int? = null
}