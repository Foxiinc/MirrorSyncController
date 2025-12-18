package com.mirrorsync.agent

import android.util.Log

/**
 * Валидатор жестов для проверки точности нажатий
 */
object GestureValidator {
    
    private const val TAG = "GestureValidator"
    
    /**
     * Минимальное расстояние для свайпа (в нормализованных координатах)
     */
    private const val MIN_SWIPE_DISTANCE = 0.05f // 5% экрана
    
    /**
     * Максимальная длительность свайпа (мс)
     */
    private const val MAX_SWIPE_DURATION = 5000
    
    /**
     * Минимальная длительность свайпа (мс)
     */
    private const val MIN_SWIPE_DURATION = 50
    
    /**
     * Проверка валидности тапа
     */
    fun validateTap(x: Float, y: Float): ValidationResult {
        val errors = mutableListOf<String>()
        
        if (x !in 0f..1f) {
            errors.add("X coordinate out of range: $x (expected 0.0-1.0)")
        }
        
        if (y !in 0f..1f) {
            errors.add("Y coordinate out of range: $y (expected 0.0-1.0)")
        }
        
        // Проверка на краях экрана (может быть проблематично)
        if (x < 0.01f || x > 0.99f) {
            Log.w(TAG, "Tap near screen edge X: $x")
        }
        
        if (y < 0.01f || y > 0.99f) {
            Log.w(TAG, "Tap near screen edge Y: $y")
        }
        
        return if (errors.isEmpty()) {
            ValidationResult.Success
        } else {
            ValidationResult.Error(errors.joinToString("; "))
        }
    }
    
    /**
     * Проверка валидности свайпа
     */
    fun validateSwipe(
        x1: Float, y1: Float,
        x2: Float, y2: Float,
        durationMs: Int
    ): ValidationResult {
        val errors = mutableListOf<String>()
        
        // Проверка координат
        if (x1 !in 0f..1f) errors.add("Start X out of range: $x1")
        if (y1 !in 0f..1f) errors.add("Start Y out of range: $y1")
        if (x2 !in 0f..1f) errors.add("End X out of range: $x2")
        if (y2 !in 0f..1f) errors.add("End Y out of range: $y2")
        
        // Проверка расстояния
        val distance = calculateDistance(x1, y1, x2, y2)
        if (distance < MIN_SWIPE_DISTANCE) {
            errors.add("Swipe distance too small: $distance (min: $MIN_SWIPE_DISTANCE)")
        }
        
        // Проверка длительности
        if (durationMs < MIN_SWIPE_DURATION) {
            errors.add("Duration too short: $durationMs ms (min: $MIN_SWIPE_DURATION)")
        }
        
        if (durationMs > MAX_SWIPE_DURATION) {
            errors.add("Duration too long: $durationMs ms (max: $MAX_SWIPE_DURATION)")
        }
        
        return if (errors.isEmpty()) {
            ValidationResult.Success
        } else {
            ValidationResult.Error(errors.joinToString("; "))
        }
    }
    
    /**
     * Вычисление расстояния между двумя точками (нормализованные координаты)
     */
    private fun calculateDistance(x1: Float, y1: Float, x2: Float, y2: Float): Float {
        val dx = x2 - x1
        val dy = y2 - y1
        return kotlin.math.sqrt(dx * dx + dy * dy)
    }
    
    /**
     * Предложить оптимальную длительность свайпа на основе расстояния
     */
    fun suggestSwipeDuration(x1: Float, y1: Float, x2: Float, y2: Float): Int {
        val distance = calculateDistance(x1, y1, x2, y2)
        
        // Базовая формула: 200ms на 10% экрана
        val baseDuration = (distance * 2000).toInt()
        
        return baseDuration.coerceIn(MIN_SWIPE_DURATION, MAX_SWIPE_DURATION)
    }
    
    sealed class ValidationResult {
        object Success : ValidationResult()
        data class Error(val message: String) : ValidationResult()
    }
}
