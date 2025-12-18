package com.mirrorsync.agent

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class LogsActivity : AppCompatActivity() {
    
    companion object {
        private const val TAG = "LogsActivity"
    }
    
    private lateinit var logsTextView: TextView
    private lateinit var clearButton: Button
    private lateinit var shareButton: Button
    private lateinit var autoScrollButton: Button
    
    private var autoScroll = true
    
    private val logListener = object : InAppLogger.LogListener {
        override fun onNewLog(entry: InAppLogger.LogEntry) {
            runOnUiThread {
                updateLogsDisplay()
            }
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_logs)
        
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Logs"
        
        logsTextView = findViewById(R.id.logsTextView)
        clearButton = findViewById(R.id.clearButton)
        shareButton = findViewById(R.id.shareButton)
        autoScrollButton = findViewById(R.id.autoScrollButton)
        
        clearButton.setOnClickListener {
            InAppLogger.clear()
            updateLogsDisplay()
            InAppLogger.i(TAG, "Logs cleared")
        }
        
        shareButton.setOnClickListener {
            shareLogs()
        }
        
        autoScrollButton.setOnClickListener {
            autoScroll = !autoScroll
            updateAutoScrollButton()
            InAppLogger.d(TAG, "Auto-scroll: $autoScroll")
        }
        
        InAppLogger.addListener(logListener)
        updateLogsDisplay()
        updateAutoScrollButton()
        startAutoRefresh()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        InAppLogger.removeListener(logListener)
    }
    
    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
    
    private fun updateLogsDisplay() {
        val logs = InAppLogger.getAllLogs()
        if (logs.isEmpty()) {
            logsTextView.text = "No logs yet..."
        } else {
            logsTextView.text = logs.joinToString("\n") { it.format() }
            
            if (autoScroll) {
                logsTextView.post {
                    val scrollView = findViewById<android.widget.ScrollView>(R.id.scrollView)
                    scrollView?.fullScroll(android.view.View.FOCUS_DOWN)
                }
            }
        }
    }
    
    private fun updateAutoScrollButton() {
        autoScrollButton.text = if (autoScroll) "Auto-scroll: ON" else "Auto-scroll: OFF"
    }
    
    private fun shareLogs() {
        val logsText = InAppLogger.getLogsAsString()
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_SUBJECT, "MirrorSync Agent Logs")
            putExtra(Intent.EXTRA_TEXT, logsText)
        }
        startActivity(Intent.createChooser(intent, "Share logs via"))
        InAppLogger.i(TAG, "Logs shared")
    }
    
    private fun startAutoRefresh() {
        lifecycleScope.launch {
            while (true) {
                delay(1000)
                updateLogsDisplay()
            }
        }
    }
}
