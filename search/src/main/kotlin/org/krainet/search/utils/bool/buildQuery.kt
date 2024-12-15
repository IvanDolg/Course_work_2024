package org.krainet.search.utils.bool

import co.elastic.clients.elasticsearch._types.query_dsl.BoolQuery
import co.elastic.clients.elasticsearch._types.query_dsl.Query
import java.util.*

fun toPolishNotation(tokens: List<String>): List<String> {
    val output = mutableListOf<String>()
    val operators = Stack<String>()

    for (token in tokens) {
        when {
            token == "(" -> {
                operators.push(token)
            }
            token == ")" -> {
                while (operators.isNotEmpty() && operators.peek() != "(") {
                    output.add(operators.pop())
                }
                operators.pop()
            }
            token.isBoolOperation() -> {
                while (operators.isNotEmpty() && precedence(operators.peek()) >= precedence(token)) {
                    output.add(operators.pop())
                }
                operators.push(token)
            }
            else -> {
                output.add(token)
            }
        }
    }

    while (operators.isNotEmpty()) {
        output.add(operators.pop())
    }

    return output
}

fun evaluateRPN(expression: List<String>): Query {
    val stack = Stack<Query>()

    for (token in expression) {
        when (token) {
            "&" -> {
                val operand1 = stack.pop()
                val operand2 = stack.pop()
                val result = BoolQuery.of { it.must(mutableListOf(operand1, operand2)) }
                stack.push(Query.of { it.bool(result) })
            }
            "|" -> {
                val operand1 = stack.pop()
                val operand2 = stack.pop()
                val result = BoolQuery.of { it.should(mutableListOf(operand1, operand2)) }
                stack.push(Query.of { it.bool(result) })
            }
            "~" -> {
                val operand1 = stack.pop()
                val result = BoolQuery.of { it.mustNot(operand1) }
                stack.push(Query.of { it.bool(result) })
            }
            else -> {
                val triple = splitString(token) ?: break
                val query = filterFabric(triple.first, triple.second, triple.third)
                stack.push(query)
            }
        }
    }

    return stack.pop()
}

fun parseQuery(query: String): Query {
    val tokens = convertBoolExpression(tokenize(query))
    val polishNotation = toPolishNotation(parseBoolExpression(tokens))
    val rootQuery = evaluateRPN(polishNotation)
    return rootQuery
}