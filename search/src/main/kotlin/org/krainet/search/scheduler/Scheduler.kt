package org.krainet.search.scheduler

import lombok.extern.slf4j.Slf4j
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Service
import java.net.HttpURLConnection
import java.net.URL
import javax.print.DocFlavor
import kotlin.math.log

@Service
class Scheduler {
    @Scheduled(cron = "0 0 0 * * *")
    fun scheduler() {
        println("Scheduler started")
        val url = URL("http://belrw-admin:8000/kservice/make-circulation")
        val connection = url.openConnection() as HttpURLConnection
        connection.requestMethod = "GET"
        val responseCode = connection.responseCode
        println("Response Code: $responseCode")
        connection.disconnect()
    }

    @Scheduled(cron = "0 0 0 * * *")
    fun schedulerMail() {
        println("Scheduler started")
        val url = URL("http://belrw-admin:8000/reregister/")
        val connection = url.openConnection() as HttpURLConnection
        connection.requestMethod = "GET"
        val responseCode = connection.responseCode
        println("Response Code: $responseCode")
        connection.disconnect()
    }
}