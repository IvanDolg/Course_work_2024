package org.krainet.search.utils

import org.krainet.search.model.enums.EDITION_SUBTYPE
import org.krainet.search.model.enums.EDITION_TYPE
import org.krainet.search.view.edition.basic.BasicQueryView
import org.krainet.search.view.edition.extended.ExtendedQueryView
import org.krainet.search.view.edition.extended.SearchExtendedView
import java.text.SimpleDateFormat
import java.util.*

fun stringToDate(dateString: String?, format: String): Date? {
    val dateFormat = SimpleDateFormat(format)
    return try {
        dateFormat.parse(dateString)
    } catch (e: Exception) {
        null
    }
}

fun dateToString(date: Date?, format: String): String? {
    if (date == null) {
        return null
    }
    val dateFormat = SimpleDateFormat(format)
    return dateFormat.format(date)
}

fun parseQueryToBasicQueryView(query: Map<String, String>): BasicQueryView {
    val q = BasicQueryView()

    q.pagination.page = query["page"]?.toInt()
    q.pagination.size = query["size"]?.toInt()

    q.filters.types = query["types"]
        ?.split(",")
        ?.mapNotNull { type ->
            try {
                EDITION_TYPE.valueOf(type)
            } catch (e: IllegalArgumentException) {
                null
            }
        }?.toMutableList() ?: mutableListOf()
    q.filters.subtypes = query["subtypes"]
        ?.split(",")
        ?.mapNotNull { type ->
            try {
                EDITION_SUBTYPE.valueOf(type)
            } catch (e: IllegalArgumentException) {
                null
            }
        }?.toMutableList() ?: mutableListOf()
    q.filters.database = if (!query["database"].isNullOrEmpty()) {
        query["database"].toString().replace("+", " ")
    } else {
        null
    }
    q.filters.pubDate.pubDateTo = stringToDate(query["pub_date_to"], "yyyy-MM-dd")
    q.filters.pubDate.pubDateFrom = stringToDate(query["pub_date_from"], "yyyy-MM-dd")

    q.search.query = query["query"]
    q.search.mode = query["mode"]
    q.search.field = query["field"]

    return q
}

fun parseQueryToExtendedQueryView(query: Map<String, String>): ExtendedQueryView {
    val q = ExtendedQueryView()

    q.pagination.page = query["page"]?.toInt()
    q.pagination.size = query["size"]?.toInt()

    q.filters.types = query["types"]
        ?.split(",")
        ?.mapNotNull { type ->
            try {
                EDITION_TYPE.valueOf(type)
            } catch (e: IllegalArgumentException) {
                null
            }
        }?.toMutableList() ?: mutableListOf()
    q.filters.subtypes = query["subtypes"]
        ?.split(",")
        ?.mapNotNull { type ->
            try {
                EDITION_SUBTYPE.valueOf(type)
            } catch (e: IllegalArgumentException) {
                null
            }
        }?.toMutableList() ?: mutableListOf()
    q.filters.databases = query["databases"]
            ?.split(",")
            ?.map { database ->
                database.replace("+", " ")
            }?.toMutableList() ?: mutableListOf()
    q.filters.pubDate.pubDateTo = stringToDate("${query["year_to"]}-12-31", "yyyy-MM-dd")
    q.filters.pubDate.pubDateFrom = stringToDate("${query["year_from"]}-01-01", "yyyy-MM-dd")

    val fieldKeys = query.keys.filter { it.startsWith("field_") }

    fieldKeys.forEach { key ->
        val fieldName = key.removePrefix("field_")
        val fieldValue = query[key]

        if (!fieldValue.isNullOrBlank()) {
            val item = SearchExtendedView(fieldValue, fieldName)
            q.search.add(item)
        }
    }

    return q
}