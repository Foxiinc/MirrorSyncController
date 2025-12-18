package com.mirrorsync.agent

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.text.TextUtils
import android.util.Log
import android.view.accessibility.AccessibilityManager
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    
    companion object {
        private const val TAG = "MainActivity"
        
        fun isAccessibilityServiceEnabled(context: Context): Boolean {
            val enabledServices = Settings.Secure.getString(
                context.contentResolver,
                Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            )
            
            val serviceName = "${context.packageName}/.MirrorAccessibilityService"
            return !TextUtils.isEmpty(enabledServices) && enabledServices.contains(serviceName)
        }
    }
    
    private lateinit var statusText: TextView
    private lateinit var enableButton: Button
    private lateinit var tcpStatusText: TextView
    private lateinit var viewLogsButton: Button
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        Log.i(TAG, "MainActivity created")
        
        statusText = findViewById(R.id.statusText)
        enableButton = findViewById(R.id.enableButton)
        tcpStatusText = findViewById(R.id.tcpStatusText)
        viewLogsButton = findViewById(R.id.viewLogsButton)
        
        enableButton.setOnClickListener {
            openAccessibilitySettings()
        }
        
        viewLogsButton.setOnClickListener {
            startActivity(Intent(this, LogsActivity::class.java))
        }
        
        InAppLogger.i(TAG, "MainActivity created")
        
        updateStatus()
        startStatusUpdates()
    }
    
    override fun onResume() {
        super.onResume()
        InAppLogger.d(TAG, "MainActivity resumed")
        updateStatus()
    }
    
    private fun startStatusUpdates() {
        lifecycleScope.launch {
            while (true) {
                updateStatus()
                delay(2000)
            }
        }
    }
    

    
    private fun updateStatus() {
        val isEnabled = isAccessibilityServiceEnabled()
        val serviceInstance = MirrorAccessibilityService.instance
        
        statusText.text = when {
            !isEnabled -> "❌ Accessibility Service: DISABLED"
            serviceInstance == null -> "⚠️ Accessibility Service: ENABLED but not running"
            else -> "✅ Accessibility Service: RUNNING"
        }
        
        tcpStatusText.text = if (serviceInstance != null) {
            "✅ TCP Server: Listening on port 4444"
        } else {
            "❌ TCP Server: Not running"
        }
        
        enableButton.isEnabled = !isEnabled
        
        InAppLogger.d(TAG, "Status: enabled=$isEnabled, instance=${serviceInstance != null}")
    }
    
    private fun openAccessibilitySettings() {
        val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
        startActivity(intent)
    }
    
    private fun isAccessibilityServiceEnabled(): Boolean {
        val accessibilityManager = getSystemService(Context.ACCESSIBILITY_SERVICE) as AccessibilityManager
        val enabledServices = accessibilityManager.getEnabledAccessibilityServiceList(AccessibilityServiceInfo.FEEDBACK_ALL_MASK)
        
        val serviceName = "${packageName}/.MirrorAccessibilityService"
        return enabledServices.any { it.id == serviceName }
    }
    
    private fun showRestrictedSettingsWarning() {
        AlertDialog.Builder(this)
            .setTitle("Важно: Restricted Settings")
            .setMessage("В Android 13+ необходимо:\n\n" +
                    "1. Перейти в Settings → Apps → MirrorSync Agent\n" +
                    "2. Нажать на три точки (⋮) → Allow restricted settings\n" +
                    "3. Включить переключатель\n" +
                    "4. Затем включить Accessibility Service\n\n" +
                    "Без этого сервис не будет работать!")
            .setPositiveButton("Понятно") { dialog, _ -> dialog.dismiss() }
            .setNegativeButton("Открыть настройки") { _, _ -> 
                openAppSettings()
            }
            .show()
    }
    
    private fun openAppSettings() {
        val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
            data = android.net.Uri.fromParts("package", packageName, null)
        }
        startActivity(intent)
    }
    
}