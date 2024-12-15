package org.krainet.search.model

class Term() {
    var field: String = ""
    var mode: String? = ""
    var value: String = ""

    constructor(field: String, mode: String?, value: String) : this() {
        this.field = field
        this.mode = mode
        this.value = value
    }

    override fun toString(): String {
        return "field=${field}; mode=${mode}; value=${value};"
    }
}