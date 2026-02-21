package com.mirrorsync.agent

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Intent
import android.graphics.Path
import android.util.Log
import android.graphics.Rect
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import kotlinx.coroutines.*
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

class MirrorAccessibilityService : AccessibilityService() {
    
    companion object {
        private const val TAG = "MirrorAccessibilityService"
        var instance: MirrorAccessibilityService? = null
    }
    
    private val serviceScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var commandQueue: CommandQueue? = null
    private lateinit var coordinateNormalizer: CoordinateNormalizer
    
    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        
        try {
            coordinateNormalizer = CoordinateNormalizer(this)
            val screenInfo = coordinateNormalizer.getScreenInfo()
            InAppLogger.i(TAG, "Screen: ${screenInfo.widthPixels}x${screenInfo.heightPixels}")
        } catch (e: Exception) {
            InAppLogger.e(TAG, "Failed to init CoordinateNormalizer", e)
        }
        
        try {
            commandQueue = CommandQueue(this, serviceScope)
            InAppLogger.i(TAG, "CommandQueue initialized")
        } catch (e: Exception) {
            InAppLogger.e(TAG, "Failed to init CommandQueue", e)
        }
        
        InAppLogger.i(TAG, "Accessibility service connected and ready")
        
        try {
            val intent = Intent(this, TcpServerService::class.java)
            startForegroundService(intent)
            InAppLogger.i(TAG, "TCP server started")
        } catch (e: Exception) {
            InAppLogger.e(TAG, "Failed to start TCP server", e)
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        
        try {
            commandQueue = null
            serviceScope.cancel()
            
            val intent = Intent(this, TcpServerService::class.java)
            stopService(intent)
            
            instance = null
            InAppLogger.i(TAG, "Service destroyed")
        } catch (e: Exception) {
            InAppLogger.e(TAG, "Error destroying service", e)
        }
    }
    
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Not needed for gesture dispatch
    }
    
    override fun onInterrupt() {
        Log.w(TAG, "Accessibility service interrupted")
    }
    
    fun executeCommand(command: DeviceCommand): DeviceResponse {
        val startTime = System.currentTimeMillis()
        
        return try {
            val currentTime = System.currentTimeMillis()
            val delayMs = command.execTimeDeviceMs - currentTime
            
            if (delayMs > 0 && delayMs < 10000) {
                Log.d(TAG, "Waiting ${delayMs}ms before executing ${command.type}")
                Thread.sleep(delayMs)
            }
            
            val success = try {
                when (command.type) {
                    "TAP" -> {
                        val hasSelector = !command.tapViewId.isNullOrBlank() ||
                                !command.tapText.isNullOrBlank() ||
                                !command.tapContentDesc.isNullOrBlank()
                        if (hasSelector) {
                            val node = findNode(command.tapViewId, command.tapText, command.tapContentDesc)
                            if (node != null) {
                                InAppLogger.d(TAG, "TAP by element: viewId=${command.tapViewId}, text=${command.tapText}, contentDesc=${command.tapContentDesc}")
                                performTapOnNode(node)
                            } else {
                                InAppLogger.e(TAG, "TAP by element: node not found")
                                false
                            }
                        } else {
                            val validation = GestureValidator.validateTap(command.x, command.y)
                            if (validation is GestureValidator.ValidationResult.Error) {
                                InAppLogger.e(TAG, "Invalid TAP: ${validation.message}")
                                false
                            } else {
                                InAppLogger.d(TAG, "TAP (${command.x}, ${command.y})")
                                performTap(command.x, command.y)
                            }
                        }
                    }
                    "SWIPE" -> {
                        val validation = GestureValidator.validateSwipe(
                            command.x, command.y, command.endX, command.endY, command.durationMs
                        )
                        if (validation is GestureValidator.ValidationResult.Error) {
                            InAppLogger.e(TAG, "Invalid SWIPE: ${validation.message}")
                            false
                        } else {
                            InAppLogger.d(TAG, "SWIPE (${command.x},${command.y})->(${command.endX},${command.endY})")
                            performSwipe(command.x, command.y, command.endX, command.endY, command.durationMs)
                        }
                    }
                    "TEXT" -> {
                        Log.d(TAG, "Executing TEXT: ${command.text}")
                        performText(command.text ?: "")
                    }
                    "KEY" -> {
                        Log.d(TAG, "Executing KEY: ${command.keyCode}")
                        performKey(command.keyCode)
                    }
                    else -> {
                        Log.w(TAG, "Unknown command type: ${command.type}")
                        false
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error executing ${command.type}: ${e.message}", e)
                false
            }
            
            val executedAt = System.currentTimeMillis()
            val totalTime = executedAt - startTime
            
            InAppLogger.i(TAG, "${command.type} seq=${command.sequence} ${if (success) "✓" else "✗"} ${totalTime}ms")
            
            DeviceResponse(
                sequence = command.sequence,
                success = success,
                message = if (success) "Executed in ${totalTime}ms" else "Failed",
                executedAtMs = executedAt
            )
        } catch (e: Exception) {
            InAppLogger.e(TAG, "Critical error in executeCommand", e)
            DeviceResponse(
                sequence = command.sequence,
                success = false,
                message = "Error: ${e.message}",
                executedAtMs = System.currentTimeMillis()
            )
        }
    }
    
    private fun performTap(x: Float, y: Float): Boolean {
        // Проверка валидности нормализованных координат
        if (!coordinateNormalizer.isValidNormalized(x, y)) {
            Log.w(TAG, "Invalid normalized coordinates: ($x, $y)")
            return false
        }
        
        // Преобразование нормализованных координат в пиксели
        val (screenX, screenY) = coordinateNormalizer.normalizedToPixels(x, y)
        
        Log.d(TAG, "Tap: normalized($x, $y) -> pixels($screenX, $screenY)")
        
        val path = Path().apply {
            moveTo(screenX, screenY)
        }
        
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 50))
            .build()
        
        var result = false
        val latch = CountDownLatch(1)
        
        val dispatched = dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                Log.d(TAG, "Tap completed at ($screenX, $screenY)")
                result = true
                latch.countDown()
            }
            
            override fun onCancelled(gestureDescription: GestureDescription?) {
                Log.w(TAG, "Tap cancelled at ($screenX, $screenY)")
                result = false
                latch.countDown()
            }
        }, null)
        
        if (!dispatched) {
            Log.e(TAG, "Failed to dispatch tap gesture")
            return false
        }
        
        val completed = latch.await(1000, TimeUnit.MILLISECONDS)
        if (!completed) {
            Log.w(TAG, "Tap gesture timeout")
        }
        
        return result
    }

    /** Поиск узла по viewId, text или contentDescription (первый подходящий). */
    private fun findNode(viewId: String?, text: String?, contentDesc: String?): AccessibilityNodeInfo? {
        val root = rootInActiveWindow ?: return null
        return findNodeRec(root, viewId, text, contentDesc)
    }

    private fun findNodeRec(node: AccessibilityNodeInfo, viewId: String?, text: String?, contentDesc: String?): AccessibilityNodeInfo? {
        if (!node.isVisibleToUser) return null
        val v = node.viewIdResourceName?.takeIf { !it.isNullOrBlank() }
        val t = node.text?.toString()?.takeIf { !it.isNullOrBlank() }
        val c = node.contentDescription?.toString()?.takeIf { !it.isNullOrBlank() }
        val matchViewId = viewId.isNullOrBlank() || v?.contains(viewId, ignoreCase = true) == true
        val matchText = text.isNullOrBlank() || t?.contains(text, ignoreCase = true) == true
        val matchDesc = contentDesc.isNullOrBlank() || c?.contains(contentDesc, ignoreCase = true) == true
        if (matchViewId && matchText && matchDesc && (node.isClickable || node.isEnabled)) return node
        for (i in 0 until node.childCount) {
            node.getChild(i)?.let { child ->
                findNodeRec(child, viewId, text, contentDesc)?.let { return it }
            }
        }
        return null
    }

    /** Тап по центру bounds узла или ACTION_CLICK. */
    private fun performTapOnNode(node: AccessibilityNodeInfo): Boolean {
        if (node.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
            Log.d(TAG, "Tap on node: ACTION_CLICK succeeded")
            return true
        }
        val rect = Rect()
        node.getBoundsInScreen(rect)
        if (rect.isEmpty) {
            Log.w(TAG, "Tap on node: bounds empty")
            return false
        }
        val centerX = rect.centerX().toFloat()
        val centerY = rect.centerY().toFloat()
        val path = Path().apply { moveTo(centerX, centerY) }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 50))
            .build()
        var result = false
        val latch = CountDownLatch(1)
        val dispatched = dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                result = true
                latch.countDown()
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                latch.countDown()
            }
        }, null)
        if (!dispatched) return false
        latch.await(1000, TimeUnit.MILLISECONDS)
        return result
    }
    
    private fun performSwipe(x1: Float, y1: Float, x2: Float, y2: Float, durationMs: Int): Boolean {
        // Проверка валидности координат
        if (!coordinateNormalizer.isValidNormalized(x1, y1) || 
            !coordinateNormalizer.isValidNormalized(x2, y2)) {
            Log.w(TAG, "Invalid swipe coordinates: ($x1,$y1) -> ($x2,$y2)")
            return false
        }
        
        // Преобразование координат
        val (startX, startY) = coordinateNormalizer.normalizedToPixels(x1, y1)
        val (endX, endY) = coordinateNormalizer.normalizedToPixels(x2, y2)
        
        Log.d(TAG, "Swipe: ($x1,$y1)->($x2,$y2) pixels: ($startX,$startY)->($endX,$endY)")
        
        val duration = durationMs.coerceIn(100, 5000).toLong()
        
        val path = Path().apply {
            moveTo(startX, startY)
            lineTo(endX, endY)
        }
        
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, duration))
            .build()
        
        var result = false
        val latch = CountDownLatch(1)
        
        val dispatched = dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                Log.d(TAG, "Swipe completed: ($startX,$startY)->($endX,$endY)")
                result = true
                latch.countDown()
            }
            
            override fun onCancelled(gestureDescription: GestureDescription?) {
                Log.w(TAG, "Swipe cancelled: ($startX,$startY)->($endX,$endY)")
                result = false
                latch.countDown()
            }
        }, null)
        
        if (!dispatched) {
            Log.e(TAG, "Failed to dispatch swipe gesture")
            return false
        }
        
        val completed = latch.await(2000, TimeUnit.MILLISECONDS)
        if (!completed) {
            Log.w(TAG, "Swipe gesture timeout")
        }
        
        return result
    }
    
    /** TEXT не поддерживается: требуется IME / ACTION_SET_TEXT; пока явно не реализовано. */
    private fun performText(text: String): Boolean {
        return try {
            Log.i(TAG, "TEXT not supported (requested: $text)")
            false
        } catch (e: Exception) {
            Log.e(TAG, "Error in performText", e)
            false
        }
    }
    
    private fun performKey(keyCode: Int): Boolean {
        return try {
            Log.i(TAG, "Performing key press: $keyCode")
            val result = when (keyCode) {
                3 -> {
                    Log.d(TAG, "Sending HOME action")
                    performGlobalAction(GLOBAL_ACTION_HOME)
                }
                4 -> {
                    Log.d(TAG, "Sending BACK action")
                    performGlobalAction(GLOBAL_ACTION_BACK)
                }
                82, 187 -> {
                    Log.d(TAG, "Sending RECENTS action")
                    performGlobalAction(GLOBAL_ACTION_RECENTS)
                }
                else -> {
                    Log.w(TAG, "Unsupported key code: $keyCode")
                    false
                }
            }
            Log.i(TAG, "Key action result: $result")
            result
        } catch (e: Exception) {
            Log.e(TAG, "Error performing key action: ${e.message}", e)
            false
        }
    }
}