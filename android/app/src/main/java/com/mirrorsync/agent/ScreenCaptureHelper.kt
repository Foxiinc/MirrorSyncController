package com.mirrorsync.agent

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Log
import java.io.InputStream

/**
 * Общий хелпер захвата экрана через screencap -p.
 * Используется TcpServerService (SCREENSHOT по TCP:4444) и ScreenStreamService (стрим на 8080).
 */
object ScreenCaptureHelper {
    private const val TAG = "ScreenCaptureHelper"

    fun capture(): Bitmap? {
        return try {
            val process = Runtime.getRuntime().exec("screencap -p")
            val inputStream: InputStream = process.inputStream
            val bitmap = BitmapFactory.decodeStream(inputStream)
            process.waitFor()
            bitmap
        } catch (e: Exception) {
            Log.e(TAG, "Screen capture failed", e)
            InAppLogger.e(TAG, "Screen capture failed", e)
            null
        }
    }
}
