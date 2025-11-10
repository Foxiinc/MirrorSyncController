package com.mirrorsync.agent

import android.app.*
import android.content.Intent
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.gson.Gson
import kotlinx.coroutines.*
import java.io.*
import java.net.ServerSocket
import java.net.Socket

class TcpServerService : Service() {
    
    companion object {
        private const val TAG = "TcpServerService"
        private const val PORT = 4444
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "MirrorSyncChannel"
    }
    
    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var serverSocket: ServerSocket? = null
    private val gson = Gson()
    
    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createNotification())
        startTcpServer()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        serviceScope.cancel()
        serverSocket?.close()
        Log.i(TAG, "TCP server stopped")
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
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
        serviceScope.launch {
            try {
                serverSocket = ServerSocket(PORT)
                Log.i(TAG, "TCP server started on port $PORT")
                
                while (!serviceScope.isActive) {
                    try {
                        val clientSocket = serverSocket?.accept()
                        if (clientSocket != null) {
                            launch { handleClient(clientSocket) }
                        }
                    } catch (e: Exception) {
                        if (serviceScope.isActive) {
                            Log.e(TAG, "Error accepting client", e)
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error starting TCP server", e)
            }
        }
    }
    
    private suspend fun handleClient(socket: Socket) {
        withContext(Dispatchers.IO) {
            try {
                val reader = BufferedReader(InputStreamReader(socket.getInputStream()))
                val writer = PrintWriter(socket.getOutputStream(), true)
                
                Log.i(TAG, "Client connected: ${socket.remoteSocketAddress}")
                
                while (socket.isConnected && !socket.isClosed) {
                    val line = reader.readLine() ?: break
                    
                    try {
                        if (line.contains("TIME_SYNC")) {
                            handleTimeSync(line, writer)
                        } else {
                            val command = gson.fromJson(line, DeviceCommand::class.java)
                            val response = executeCommand(command)
                            writer.println(gson.toJson(response))
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "Error processing command: $line", e)
                        val errorResponse = DeviceResponse(
                            sequence = 0,
                            success = false,
                            message = "Parse error: ${e.message}"
                        )
                        writer.println(gson.toJson(errorResponse))
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error handling client", e)
            } finally {
                socket.close()
                Log.i(TAG, "Client disconnected")
            }
        }
    }
    
    private fun handleTimeSync(line: String, writer: PrintWriter) {
        try {
            val request = gson.fromJson(line, TimeSync::class.java)
            val response = TimeSync(
                clientTime = request.clientTime,
                serverTime = System.currentTimeMillis()
            )
            writer.println(gson.toJson(response))
        } catch (e: Exception) {
            Log.e(TAG, "Error handling time sync", e)
        }
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