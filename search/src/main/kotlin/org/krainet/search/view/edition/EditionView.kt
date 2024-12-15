package org.krainet.search.view.edition

import com.fasterxml.jackson.annotation.JsonFormat
import com.fasterxml.jackson.annotation.JsonInclude
import com.fasterxml.jackson.annotation.JsonProperty
import org.krainet.search.model.enums.EDITION_SUBTYPE
import org.krainet.search.model.enums.EDITION_TYPE
import org.krainet.search.utils.dateToString
import java.util.*

@JsonInclude(JsonInclude.Include.NON_NULL)
class EditionView() {

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

    @JsonProperty("year")
    var year: String? = null

    @JsonProperty("note")
    var note: String? = null

    @JsonProperty("international_number")
    var internationalNumber: String? = null

    @JsonProperty("index")
    var index: String? = null

    @JsonProperty("document_number")
    var documentNumber: String? = null

    @JsonProperty("responsibility_info")
    var responsibilityInfo: String? = null

    @JsonProperty("parallel_title")
    var parallelTitle: String? = null

    @JsonProperty("designation")
    var designation: String? = null

    @JsonProperty("title_info")
    var titleInfo: String? = null

    @JsonProperty("part_number")
    var partNumber: String? = null

    @JsonProperty("part_name")
    var partName: String? = null

    @JsonProperty("author")
    var author: String? = null

    @JsonProperty("place_of_publication")
    var placeOfPublication: String? = null

    @JsonProperty("publisher")
    var publisher: String? = null

    @JsonProperty("date_of_publication")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
    var dateOfPublication: Date? = null

    @JsonProperty("series_title")
    var seriesTitle: String? = null

    @JsonProperty("edition_info")
    var editionInfo: String? = null

    @JsonProperty("volume")
    var volume: String? = null

    @JsonProperty("information_carrier")
    var informationCarrier: String? = null

    constructor(edition: EditionIndexView) : this() {
        id = edition.id
        type = edition.type
        subtype = edition.subtype
        database = edition.database
        year = if (edition.type == EDITION_TYPE.PERIODICAL) {
            dateToString(edition.dateOfPublication, "yyyy")
        } else {
            null
        }
        note = edition.note
        title = edition.title
        internationalNumber = edition.internationalNumber
        index = edition.index
        documentNumber = edition.documentNumber
        responsibilityInfo = edition.responsibilityInfo
        parallelTitle = edition.parallelTitle
        designation = edition.designation
        titleInfo = edition.titleInfo
        partNumber = edition.partNumber
        partName = edition.partName
        author = edition.author
        placeOfPublication = edition.placeOfPublication
        publisher = edition.publisher
        dateOfPublication = if (edition.type == EDITION_TYPE.PERIODICAL){
            null
        } else {
            edition.dateOfPublication
        }
        seriesTitle = edition.seriesTitle
        editionInfo = edition.editionInfo
        volume = edition.volume
        informationCarrier = edition.informationCarrier
    }
}