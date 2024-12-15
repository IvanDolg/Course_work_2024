package org.krainet.search.view.sku

import SkuIndexView
import com.fasterxml.jackson.annotation.JsonFormat
import com.fasterxml.jackson.annotation.JsonInclude
import com.fasterxml.jackson.annotation.JsonProperty
import org.krainet.search.model.enums.EDITION_SUBTYPE
import org.krainet.search.model.enums.EDITION_TYPE
import org.krainet.search.utils.dateToString
import java.util.*

@JsonInclude(JsonInclude.Include.NON_NULL)
class SkuView() {
    @JsonProperty("id")
    var id: Long = 0

    @JsonProperty("type")
    var type: EDITION_TYPE = EDITION_TYPE.PERIODICAL

    @JsonProperty("subtype")
    var subtype: EDITION_SUBTYPE = EDITION_SUBTYPE.BOOK

    @JsonProperty("database")
    var database: String = ""

    @JsonProperty("title")
    var title: String? = null

    @JsonProperty("date_of_publication")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
    var dateOfPublication: Date? = null

    @JsonProperty("year")
    var year: String? = null

    @JsonProperty("note")
    var note: String? = null

    @JsonProperty("author")
    var author: String? = null

    @JsonProperty("subject")
    var subject: String? = null

    @JsonProperty("is_published")
    var isPublished: Boolean? = null

    constructor(sku: SkuIndexView) : this() {
        id = sku.id
        type = sku.type
        subtype = sku.subtype
        database = sku.database
        note = sku.note
        title = sku.title
        author = sku.author
        year = if (sku.type == EDITION_TYPE.PERIODICAL) {
            dateToString(sku.dateOfPublication, "yyyy")
        } else {
            null
        }
        dateOfPublication = if (sku.type == EDITION_TYPE.PERIODICAL){
            null
        } else {
            sku.dateOfPublication
        }
        subject = sku.subject
        isPublished = sku.isPublished
    }
}