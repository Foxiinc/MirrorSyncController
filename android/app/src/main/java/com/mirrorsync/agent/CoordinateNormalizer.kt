package com.mirrorsync.agent

import android.content.Context
import android.content.res.Configuration
import android.graphics.Point
import android.util.DisplayMetrics
import android.util.Log
import android.view.WindowManager

/**
 * Правильная нормализация координат для всех Android устройств
 * Учитывает: плотность экрана, ориентацию, вырезы, системные панели
 */
class CoordinateNormalizer(private val context: Context) {
    
    companion object {
        private const val TAG = "CoordinateNormalizer"
    }
    
    private val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private val displayMetrics = context.resources.displayMetrics
    
    data class ScreenInfo(
        val widthPixels: Int,
        val heightPixels: Int,
        val densityDpi: Int,
        val density: Float,
        val orientation: Int,
        val isPortrait: Boolean
    )
    
    /**
     * Получить информацию о экране
     */
    fun getScreenInfo(): ScreenInfo {
        val display = windowManager.defaultDisplay
        val realSize = Point()
        display.getRealSize(realSize)
        
        val orientation = context.resources.configuration.orientation
        val isPortrait = orientation == Configuration.ORIENTATION_PORTRAIT
        
        return ScreenInfo(
            widthPixels = realSize.x,
            heightPixels = realSize.y,
            densityDpi = displayMetrics.densityDpi,
            density = displayMetrics.density,
            orientation = orientation,
            isPortrait = isPortrait
        ).also {
            Log.d(TAG, "Screen: ${it.widthPixels}x${it.heightPixels}, " +
                    "density=${it.density}, dpi=${it.densityDpi}, " +
                    "orientation=${if (it.isPortrait) "portrait" else "landscape"}")
        }
    }
    
    /**
     * Нормализованные координаты (0.0-1.0) -> Пиксели экрана
     * 
     * @param normalizedX координата X в диапазоне 0.0-1.0
     * @param normalizedY координата Y в диапазоне 0.0-1.0
     * @return Pair(pixelX, pixelY)
     */
    fun normalizedToPixels(normalizedX: Float, normalizedY: Float): Pair<Float, Float> {
        val screenInfo = getScreenInfo()
        
        // Проверка диапазона
        val clampedX = normalizedX.coerceIn(0f, 1f)
        val clampedY = normalizedY.coerceIn(0f, 1f)
        
        // Преобразование в пиксели
        val pixelX = clampedX * screenInfo.widthPixels
        val pixelY = clampedY * screenInfo.heightPixels
        
        // Убедимся что координаты в пределах экрана
        val finalX = pixelX.coerceIn(0f, screenInfo.widthPixels.toFloat())
        val finalY = pixelY.coerceIn(0f, screenInfo.heightPixels.toFloat())
        
        Log.d(TAG, "Normalized ($normalizedX, $normalizedY) -> Pixels ($finalX, $finalY)")
        
        return Pair(finalX, finalY)
    }
    
    /**
     * Пиксели экрана -> Нормализованные координаты (0.0-1.0)
     */
    fun pixelsToNormalized(pixelX: Float, pixelY: Float): Pair<Float, Float> {
        val screenInfo = getScreenInfo()
        
        val normalizedX = (pixelX / screenInfo.widthPixels).coerceIn(0f, 1f)
        val normalizedY = (pixelY / screenInfo.heightPixels).coerceIn(0f, 1f)
        
        return Pair(normalizedX, normalizedY)
    }
    
    /**
     * Проверка что координаты валидны
     */
    fun isValidNormalized(x: Float, y: Float): Boolean {
        return x in 0f..1f && y in 0f..1f
    }
    
    /**
     * Проверка что пиксельные координаты в пределах экрана
     */
    fun isValidPixels(x: Float, y: Float): Boolean {
        val screenInfo = getScreenInfo()
        return x in 0f..screenInfo.widthPixels.toFloat() && 
               y in 0f..screenInfo.heightPixels.toFloat()
    }
    
    /**
     * Получить безопасную зону для нажатий (избегая системных панелей)
     * Возвращает нормализованные координаты границ безопасной зоны
     */
    fun getSafeArea(): SafeArea {
        val screenInfo = getScreenInfo()
        
        // Примерные отступы для системных панелей
        val statusBarHeight = getStatusBarHeight()
        val navigationBarHeight = getNavigationBarHeight()
        
        val topOffset = statusBarHeight.toFloat() / screenInfo.heightPixels
        val bottomOffset = navigationBarHeight.toFloat() / screenInfo.heightPixels
        
        return SafeArea(
            left = 0f,
            top = topOffset,
            right = 1f,
            bottom = 1f - bottomOffset
        ).also {
            Log.d(TAG, "Safe area: top=$topOffset, bottom=${1f - bottomOffset}")
        }
    }
    
    data class SafeArea(
        val left: Float,
        val top: Float,
        val right: Float,
        val bottom: Float
    )
    
    private fun getStatusBarHeight(): Int {
        var result = 0
        val resourceId = context.resources.getIdentifier("status_bar_height", "dimen", "android")
        if (resourceId > 0) {
            result = context.resources.getDimensionPixelSize(resourceId)
        }
        return result
    }
    
    private fun getNavigationBarHeight(): Int {
        var result = 0
        val resourceId = context.resources.getIdentifier("navigation_bar_height", "dimen", "android")
        if (resourceId > 0) {
            result = context.resources.getDimensionPixelSize(resourceId)
        }
        return result
    }
}
