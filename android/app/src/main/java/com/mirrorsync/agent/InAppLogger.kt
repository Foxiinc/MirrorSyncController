package com.mirrorsync.agent

import android.util.Log
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.ConcurrentLinkedQueue

/**
 * Встроенный логгер для отображения логов в приложении
 */
object InAppLogger {
    
    private const val MAX_LOGS = 500
    private val logs = ConcurrentLinkedQueue<LogEntry>()
    private val listeners = mutableListOf<LogListener>()
    private val dateFormat = SimpleDateFormat("HH:mm:ss.SSS", Locale.getDefault())
    
    data class LogEntry(
        val timestamp: Long,
        val level: LogLevel,
        val tag: String,
        val message: String
    ) {
        fun format(): String {
            val time = dateFormat.format(Date(timestamp))
            val levelStr = when (level) {
                LogLevel.DEBUG -> "D"
                LogLevel.INFO -> "I"
                LogLevel.WARN -> "W"
                LogLevel.ERROR -> "E"
            }
            return "$time $levelStr/$tag: $message"
        }
    }
    
    enum class LogLevel {
        DEBUG, INFO, WARN, ERROR
    }
    
    interface LogListener {
        fun onNewLog(entry: LogEntry)
    }
    
    fun d(tag: String, message: String) {
        log(LogLevel.DEBUG, tag, message)
        Log.d(tag, message)
    }
    
    fun i(tag: String, message: String) {
        log(LogLevel.INFO, tag, message)
        Log.i(tag, message)
    }
    
    fun w(tag: String, message: String) {
        log(LogLevel.WARN, tag, message)
        Log.w(tag, message)
    }
    
    fun e(tag: String, message: String, throwable: Throwable? = null) {
        val msg = if (throwable != null) {
            "$message: ${throwable.message}"
        } else {
            message
        }
        log(LogLevel.ERROR, tag, msg)
        if (throwable != null) {
            Log.e(tag, message, throwable)
        } else {
            Log.e(tag, message)
        }
    }
    
    private fun log(level: LogLevel, tag: String, message: String) {
        val entry = LogEntry(System.currentTimeMillis(), level, tag, message)
        
        logs.add(entry)
        
        // Ограничение размера
        while (logs.size > MAX_LOGS) {
            logs.poll()
        }
        
        // Уведомление слушателей
        listeners.forEach { it.onNewLog(entry) }
    }
    
    fun addListener(listener: LogListener) {
        listeners.add(listener)
    }
    
    fun removeListener(listener: LogListener) {
        listeners.remove(listener)
    }
    
    fun getAllLogs(): List<LogEntry> = logs.toList()
    
    fun getLogsAsString(): String = logs.joinToString("\n") { it.format() }
    
    fun clear() {
        logs.clear()
    }
    
    fun getLogsByLevel(level: LogLevel): List<LogEntry> {
        return logs.filter { it.level == level }
    }
    
    fun getLogsByTag(tag: String): List<LogEntry> {
        return logs.filter { it.tag == tag }
    }
}
