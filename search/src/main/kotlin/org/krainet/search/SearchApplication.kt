package org.krainet.search

import org.slf4j.Logger
import org.slf4j.LoggerFactory
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.scheduling.annotation.EnableScheduling

@SpringBootApplication
@EnableScheduling
class SearchApplication

fun main(args: Array<String>) {
	runApplication<SearchApplication>(*args)
}

inline fun <reified T> getMyLogger(): Logger {
	return LoggerFactory.getLogger(T::class.java)
}