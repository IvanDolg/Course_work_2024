package org.krainet.search.view

import org.krainet.search.view.edition.EditionView


class SelectionView<T> {
    var elements: MutableList<T> = mutableListOf()
    var size: Long = 0
    var page: Int? = null
    var pageSize: Int? = null
}