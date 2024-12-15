package org.krainet.search.model

import co.elastic.clients.json.JsonData

class Range(
    var gt: JsonData? = null,
    var gte: JsonData? = null,
    var lt: JsonData? = null,
    var lte: JsonData? = null,
    var from: String? = null,
    var to: String? = null
) {
    override fun toString(): String {
        return "gt=${gt.toString()}; gte=${gte.toString()}; lt=${lt.toString()}; lte=${lte.toString()}; " +
                "from=${from.toString()}; to=${to.toString()};"
    }
}