package org.krainet.search.utils.bool

import co.elastic.clients.elasticsearch._types.query_dsl.BoolQuery
import co.elastic.clients.elasticsearch._types.query_dsl.Query
import java.util.*

fun String.convertBoolOperation(): String {
    return when (this) {
        "NOT" -> "~"
        "AND" -> "&"
        "OR" -> "|"
        else -> this
    }
}

fun String.isBoolOperation(): Boolean {
    return this in setOf("~", "&", "|")
}

fun tokenize(query: String): MutableList<String> {
    val tokens = mutableListOf<String>()

    var substr = StringBuilder()
    var isInQuotes = false
    for (symbol in query) {
        substr = substr.append(symbol)

        if (symbol == '"') {
            isInQuotes = isInQuotes.not()
            continue
        }

        if (!isInQuotes && symbol == ' ') {
            tokens.add(substr.toString().trim())
            substr.clear()
        }
    }
    if (substr.isNotEmpty()) {
        tokens.add(substr.toString().trim())
    }

    return tokens
}

fun convertBoolExpression(tokens: MutableList<String>): MutableList<String> {
    return tokens.map { it.convertBoolOperation() }.toMutableList()
}

fun parseBoolExpression(tokens: MutableList<String>): MutableList<String> {
    val newTokens = mutableListOf<String>()
    val regex = Regex("""(\w+)=["](.*?)["]""")

    for (token in tokens) {
        val match = regex.find(token)
        if (match != null) {
            val field = match.groupValues[1]
            val expression = match.groupValues[2]

            if (expression.contains("&") || expression.contains("|")) {
                val operator = when {
                    expression.contains("&") -> "&"
                    expression.contains("|") -> "|"
                    else -> null
                }

                if (operator != null) {
                    val parts = expression.split(" $operator ").map { it.trim() }

                    newTokens.add("(")

                    for ((index, part) in parts.withIndex()) {
                        newTokens.add("$field=$part")
                        if (index < parts.size - 1) {
                            newTokens.add(operator)
                        }
                    }
                    newTokens.add(")")
                } else {
                    newTokens.add(token)
                }
            } else {
                newTokens.add(token)
            }
        } else {
            newTokens.add(token)
        }
    }
    return newTokens
}

fun precedence(op: String): Int {
    return when (op) {
        "~" -> 3
        "&" -> 2
        "|" -> 1
        else -> 0
    }
}

fun splitString(input: String): Triple<String, String, String>? {
    val regex = Regex("(.*?)\\s*(=|>=|<=|>|<)\\s*(.*)")
    val matchResult = regex.find(input)
    return matchResult?.destructured?.let { (left, operator, right) -> Triple(left, operator, right) }
}

fun parseMode(field: String, preMode: String?, value: String): String {
    return when(preMode) {
        "=" -> if (field.startsWith("w")) "wildcard" else if (value.last() == '?') "prefix" else "match"
        "<" -> "range"
        ">" -> "range"
        "<=" -> "range"
        ">=" -> "range"
        else -> ""
    }
}

fun convertToRangeValue(preMode: String?, preValue: String): MutableList<String> {
    val value = when(preMode) {
        "<" -> "lt(${preValue})"
        ">" -> "gt(${preValue})"
        "<=" -> "lte(${preValue})"
        ">=" -> "gte(${preValue})"
        else -> preValue
    }
    return mutableListOf(value)
}