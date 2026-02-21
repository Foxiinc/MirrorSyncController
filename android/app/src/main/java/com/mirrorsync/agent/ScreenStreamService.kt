package com.mirrorsync.agent

import android.app.Service
import android.content.Intent
import android.graphics.Bitmap
import android.os.IBinder
import android.util.Log
import kotlinx.coroutines.*
import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.net.ServerSocket
import java.net.Socket

class ScreenStreamService : Service() {
    companion object {
        private const val TAG = "ScreenStreamService"
    }
    
    private var serverSocket: ServerSocket? = null
    private var clientSocket: Socket? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startStreaming()
        return START_STICKY
    }
    
    private fun startStreaming() {
        scope.launch {
            try {
                serverSocket = ServerSocket(8080)
                Log.i(TAG, "ScreenStream server started on port 8080")
                InAppLogger.i(TAG, "ScreenStream server started on port 8080")
                
                while (true) {
                    Log.d(TAG, "Waiting for client connection...")
                    clientSocket = serverSocket?.accept()
                    Log.i(TAG, "Client connected: ${clientSocket?.inetAddress}")
                    InAppLogger.i(TAG, "Client connected from ${clientSocket?.inetAddress}")
                    clientSocket?.let { client ->
                        Log.i(TAG, "Starting stream for client")
                        streamToClient(client)
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "ScreenStream error: ${e.message}")
                InAppLogger.e(TAG, "ScreenStream error: ${e.message}")
                e.printStackTrace()
            }
        }
    }
    
    private suspend fun streamToClient(socket: Socket) = withContext(Dispatchers.IO) {
        var frameCount = 0
        try {
            val output = DataOutputStream(socket.getOutputStream())
            Log.i(TAG, "Starting stream to client")
            
            while (socket.isConnected) {
                val screenshot = ScreenCaptureHelper.capture()
                if (screenshot != null) {
                    val stream = ByteArrayOutputStream()
                    screenshot.compress(Bitmap.CompressFormat.JPEG, 80, stream)
                    val data = stream.toByteArray()
                    
                    // Отправляем размер как 4 байта big-endian
                    output.writeInt(data.size)
                    output.write(data)
                    output.flush()
                    
                    frameCount++
                    if (frameCount % 60 == 0) {
                        Log.d(TAG, "Sent $frameCount frames")
                    }
                } else {
                    Log.w(TAG, "Failed to capture screenshot")
                }
                delay(16) // ~60 FPS
            }
        } catch (e: Exception) {
            Log.e(TAG, "Stream error: ${e.message}")
            InAppLogger.e(TAG, "Stream error: ${e.message}")
            e.printStackTrace()
        } finally {
            socket.close()
            Log.i(TAG, "Client disconnected, sent $frameCount frames")
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        Log.i(TAG, "ScreenStreamService destroyed")
        scope.cancel()
        clientSocket?.close()
        serverSocket?.close()
    }
}
