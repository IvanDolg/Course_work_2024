package org.krainet.search.view.edition.basic

import com.fasterxml.jackson.annotation.JsonProperty
import org.krainet.search.model.enums.EDITION_SUBTYPE
import org.krainet.search.model.enums.EDITION_TYPE

class BasicFilterView {

    @JsonProperty("types")
    var types: MutableList<EDITION_TYPE> = mutableListOf()

    @JsonProperty("subtypes")
    var subtypes: MutableList<EDITION_SUBTYPE> = mutableListOf()

    @JsonProperty("database")
    var database: String? = ""

    @JsonProperty("pub_date")
    var pubDate: PubDateBasicView = PubDateBasicView()

    override fun toString(): String {
        return "documentTypes=${subtypes.toString()}, database=${database}, pubDate=(${pubDate.toString()})"
    }
}