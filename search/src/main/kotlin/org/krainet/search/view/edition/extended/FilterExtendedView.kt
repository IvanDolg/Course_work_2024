package org.krainet.search.view.edition.extended

import com.fasterxml.jackson.annotation.JsonProperty
import org.krainet.search.model.enums.EDITION_SUBTYPE
import org.krainet.search.model.enums.EDITION_TYPE
import org.krainet.search.view.edition.basic.PubDateBasicView
import org.krainet.search.view.edition.extended.PubDateExtendedView

class FilterExtendedView {
    @JsonProperty("types")
    var types: MutableList<EDITION_TYPE> = mutableListOf()

    @JsonProperty("subtypes")
    var subtypes: MutableList<EDITION_SUBTYPE> = mutableListOf()

    @JsonProperty("databases")
    var databases: MutableList<String> = mutableListOf()

    @JsonProperty("pub_date")
    var pubDate: PubDateBasicView = PubDateBasicView()
}