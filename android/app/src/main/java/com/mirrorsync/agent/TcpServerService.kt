package com.mirrorsync.agent

import android.app.*
import android.content.Intent
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleService
import androidx.lifecycle.lifecycleScope
import com.google.gson.Gson
import kotlinx.coroutines.*
import java.io.*
import java.net.ServerSocket
import java.net.Socket
import java.net.SocketTimeoutException

class TcpServerService : LifecycleService() {
    
    companion object {
        private const val TAG = "TcpServerService"
        private const val PORT = 4444
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "MirrorSyncChannel"
        private const val SOCKET_TIMEOUT = 30000
    }
    
    private var serverSocket: ServerSocket? = null
    private val gson = Gson()
    private val activeClients = mutableListOf<Socket>()
    
    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createNotification())
        startTcpServer()
        InAppLogger.i(TAG, "TCP Service created")
    }
    
    override fun onDestroy() {
        super.onDestroy()
        activeClients.forEach { it.close() }
        activeClients.clear()
        serverSocket?.close()
        InAppLogger.i(TAG, "TCP server stopped")
    }
    
    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "MirrorSync Service",
            NotificationManager.IMPORTANCE_LOW
        )
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }
    
    private fun createNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("MirrorSync Agent")
            .setContentText("TCP server running on port $PORT")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .build()
    }
    
    private fun startTcpServer() {
        lifecycleScope.launch(Dispatchers.IO) {
            try {
                serverSocket = ServerSocket(PORT).apply {
                    soTimeout = SOCKET_TIMEOUT
                }
                InAppLogger.i(TAG, "TCP server listening on port $PORT")
                updateNotification("Listening on port $PORT")
                
                while (isActive) {
                    try {
                        val clientSocket = serverSocket?.accept()
                        if (clientSocket != null) {
                            activeClients.add(clientSocket)
                            launch { handleClient(clientSocket) }
                            updateNotification("${activeClients.size} client(s) connected")
                        }
                    } catch (e: SocketTimeoutException) {
                        // Timeout - продолжаем слушать
                    } catch (e: Exception) {
                        if (isActive) {
                            InAppLogger.e(TAG, "Error accepting client", e)
                        }
                    }
                }
            } catch (e: Exception) {
                InAppLogger.e(TAG, "Error starting TCP server", e)
                updateNotification("Error: ${e.message}")
            }
        }
    }
    
    private suspend fun handleClient(socket: Socket) {
        withContext(Dispatchers.IO) {
            var reader: BufferedReader? = null
            var writer: PrintWriter? = null
            
            try {
                socket.soTimeout = 60000 // 60 секунд таймаут для чтения
                reader = BufferedReader(InputStreamReader(socket.getInputStream()))
                writer = PrintWriter(socket.getOutputStream(), true)
                
                InAppLogger.i(TAG, "Client connected: ${socket.remoteSocketAddress}")
                
                while (isActive && socket.isConnected && !socket.isClosed) {
                    try {
                        val line = reader.readLine() ?: break
                        
                        when {
                            line.contains("TIME_SYNC") -> handleTimeSync(line, writer)
                            line.contains("PING") -> {
                                writer.println("{\"type\":\"PONG\",\"success\":true}")
                                InAppLogger.d(TAG, "PING -> PONG")
                            }
                            line.contains("SCREENSHOT") -> handleScreenshot(socket)
                            else -> {
                                val command = gson.fromJson(line, DeviceCommand::class.java)
                                val response = executeCommand(command)
                                writer.println(gson.toJson(response))
                            }
                        }
                    } catch (e: SocketTimeoutException) {
                        InAppLogger.w(TAG, "Socket timeout")
                        break
                    } catch (e: Exception) {
                        InAppLogger.e(TAG, "Error processing command", e)
                        val errorResponse = DeviceResponse(
                            sequence = 0,
                            success = false,
                            message = "Error: ${e.message}"
                        )
                        writer.println(gson.toJson(errorResponse))
                    }
                }
            } catch (e: Exception) {
                InAppLogger.e(TAG, "Error handling client", e)
            } finally {
                try {
                    reader?.close()
                    writer?.close()
                    socket.close()
                    activeClients.remove(socket)
                    updateNotification("${activeClients.size} client(s) connected")
                } catch (e: Exception) {
                    InAppLogger.e(TAG, "Error closing socket", e)
                }
                InAppLogger.i(TAG, "Client disconnected")
            }
        }
    }
    
    private fun handleScreenshot(socket: Socket) {
        try {
            val bitmap = ScreenCaptureHelper.capture()
            if (bitmap == null) {
                InAppLogger.w(TAG, "Screenshot capture failed")
                return
            }
            val stream = ByteArrayOutputStream()
            bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, 80, stream)
            val data = stream.toByteArray()
            val output = DataOutputStream(socket.getOutputStream())
            output.writeInt(data.size)
            output.writeInt(bitmap.width)
            output.writeInt(bitmap.height)
            output.write(data)
            output.flush()
            InAppLogger.d(TAG, "Screenshot sent: ${bitmap.width}x${bitmap.height}, ${data.size} bytes")
        } catch (e: Exception) {
            InAppLogger.e(TAG, "Screenshot failed", e)
        }
    }

    private fun handleTimeSync(line: String, writer: PrintWriter) {
        try {
            val request = gson.fromJson(line, TimeSync::class.java)
            val serverTime = System.currentTimeMillis()
            val response = TimeSync(
                clientTime = request.clientTime,
                serverTime = serverTime
            )
            writer.println(gson.toJson(response))
            InAppLogger.d(TAG, "Time sync: offset=${serverTime - request.clientTime}ms")
        } catch (e: Exception) {
            InAppLogger.e(TAG, "Time sync error", e)
        }
    }
    
    private fun updateNotification(text: String) {
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("MirrorSync Agent")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .build()
        
        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.notify(NOTIFICATION_ID, notification)
    }
    
    private fun executeCommand(command: DeviceCommand): DeviceResponse {
        val accessibilityService = MirrorAccessibilityService.instance
        
        return if (accessibilityService != null) {
            accessibilityService.executeCommand(command)
        } else {
            DeviceResponse(
                sequence = command.sequence,
                success = false,
                message = "Accessibility service not available"
            )
        }
    }
}