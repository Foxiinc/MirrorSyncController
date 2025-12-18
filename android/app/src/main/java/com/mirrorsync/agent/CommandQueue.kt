package com.mirrorsync.agent

import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
import java.util.concurrent.ConcurrentLinkedQueue

class CommandQueue(
    private val accessibilityService: MirrorAccessibilityService,
    private val scope: CoroutineScope
) {
    companion object {
        private const val TAG = "CommandQueue"
    }
    
    private val commandChannel = Channel<DeviceCommand>(Channel.UNLIMITED)
    private val pendingCommands = ConcurrentLinkedQueue<DeviceCommand>()
    
    init {
        scope.launch {
            for (command in commandChannel) {
                pendingCommands.offer(command)
            }
        }
        
        scope.launch {
            while (isActive) {
                processBatch()
                delay(10)
            }
        }
    }
    
    suspend fun enqueue(command: DeviceCommand) {
        commandChannel.send(command)
    }
    
    private fun processBatch() {
        val batch = mutableListOf<DeviceCommand>()
        val currentTime = System.currentTimeMillis()
        
        while (pendingCommands.isNotEmpty()) {
            val cmd = pendingCommands.peek() ?: break
            if (cmd.execTimeDeviceMs <= currentTime) {
                batch.add(pendingCommands.poll()!!)
            } else {
                break
            }
        }
        
        if (batch.isNotEmpty()) {
            Log.d(TAG, "Processing batch of ${batch.size} commands")
            batch.forEach { cmd ->
                accessibilityService.executeCommand(cmd)
            }
        }
    }
}
