package org.krainet.search.view.edition.basic

import com.fasterxml.jackson.annotation.JsonFormat
import com.fasterxml.jackson.annotation.JsonProperty
import lombok.ToString
import org.krainet.search.utils.stringToDate
import java.util.*

class PubDateBasicView() {
    @JsonProperty("pub_date_from")
    var pubDateFrom: Date? = null

    @JsonProperty("pub_date_to")
    var pubDateTo: Date? = null

    constructor(pubDateFrom: String?, pubDateTo: String?) : this() {
        this.pubDateFrom = stringToDate(pubDateFrom, "yyyy-MM-dd")
        this.pubDateTo = stringToDate(pubDateTo, "yyyy-MM-dd")
    }

    override fun toString(): String {
        return "pubDateFrom=${pubDateFrom}, pubDateTo=${pubDateTo}"
    }
}