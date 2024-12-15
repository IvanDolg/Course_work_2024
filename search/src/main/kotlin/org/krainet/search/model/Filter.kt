package org.krainet.search.model

class Filter() {
    var field: String = ""
    var mode: String? = ""
    var value: MutableList<String> = mutableListOf()

    constructor(field: String, mode: String?, value: MutableList<String>) : this() {
        this.field = field
        this.mode = mode
        this.value = value
    }

    override fun toString(): String {
        return "field=${field}; mode=${mode}; value=${value};"
    }
}