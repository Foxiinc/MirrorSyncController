package com.mirrorsync.agent

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Intent
import android.graphics.Path
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import kotlinx.coroutines.*

class MirrorAccessibilityService : AccessibilityService() {
    
    companion object {
        private const val TAG = "MirrorAccessibilityService"
        var instance: MirrorAccessibilityService? = null
    }
    
    private val serviceScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    
    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.i(TAG, "Accessibility service connected")
        
        // Start TCP server
        val intent = Intent(this, TcpServerService::class.java)
        startForegroundService(intent)
    }
    
    override fun onDestroy() {
        super.onDestroy()
        instance = null
        serviceScope.cancel()
        
        // Stop TCP server
        val intent = Intent(this, TcpServerService::class.java)
        stopService(intent)
        
        Log.i(TAG, "Accessibility service destroyed")
    }
    
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Not needed for gesture dispatch
    }
    
    override fun onInterrupt() {
        Log.w(TAG, "Accessibility service interrupted")
    }
    
    fun executeCommand(command: DeviceCommand): DeviceResponse {
        return try {
            val currentTime = System.currentTimeMillis()
            val delayMs = command.execTimeDeviceMs - currentTime
            
            if (delayMs > 0) {
                Thread.sleep(delayMs)
            }
            
            val success = when (command.type) {
                "TAP" -> performTap(command.x, command.y)
                "SWIPE" -> performSwipe(command.x, command.y, command.endX, command.endY, command.durationMs)
                "TEXT" -> performText(command.text ?: "")
                "KEY" -> performKey(command.keyCode)
                else -> false
            }
            
            DeviceResponse(
                sequence = command.sequence,
                success = success,
                message = if (success) "Command executed" else "Command failed",
                executedAtMs = System.currentTimeMillis()
            )
        } catch (e: Exception) {
            Log.e(TAG, "Error executing command", e)
            DeviceResponse(
                sequence = command.sequence,
                success = false,
                message = "Error: ${e.message}",
                executedAtMs = System.currentTimeMillis()
            )
        }
    }
    
    private fun performTap(x: Float, y: Float): Boolean {
        val displayMetrics = resources.displayMetrics
        val screenX = (x * displayMetrics.widthPixels).toInt()
        val screenY = (y * displayMetrics.heightPixels).toInt()
        
        val path = Path().apply {
            moveTo(screenX.toFloat(), screenY.toFloat())
        }
        
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 50))
            .build()
        
        return dispatchGesture(gesture, null, null)
    }
    
    private fun performSwipe(x1: Float, y1: Float, x2: Float, y2: Float, durationMs: Int): Boolean {
        val displayMetrics = resources.displayMetrics
        val startX = (x1 * displayMetrics.widthPixels).toInt()
        val startY = (y1 * displayMetrics.heightPixels).toInt()
        val endX = (x2 * displayMetrics.widthPixels).toInt()
        val endY = (y2 * displayMetrics.heightPixels).toInt()
        
        val path = Path().apply {
            moveTo(startX.toFloat(), startY.toFloat())
            lineTo(endX.toFloat(), endY.toFloat())
        }
        
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, durationMs.toLong()))
            .build()
        
        return dispatchGesture(gesture, null, null)
    }
    
    private fun performText(text: String): Boolean {
        // Text input would require additional implementation
        // For now, return true as placeholder
        Log.i(TAG, "Text input: $text")
        return true
    }
    
    private fun performKey(keyCode: Int): Boolean {
        // Key press would require additional implementation
        // For now, return true as placeholder
        Log.i(TAG, "Key press: $keyCode")
        return true
    }
}