package com.mirrorsync.agent

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    
    private lateinit var statusText: TextView
    private lateinit var enableButton: Button
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        statusText = findViewById(R.id.statusText)
        enableButton = findViewById(R.id.enableButton)
        
        enableButton.setOnClickListener {
            openAccessibilitySettings()
        }
        
        updateStatus()
    }
    
    override fun onResume() {
        super.onResume()
        updateStatus()
    }
    
    private fun updateStatus() {
        val isEnabled = MirrorAccessibilityService.instance != null
        
        statusText.text = if (isEnabled) {
            getString(R.string.service_running)
        } else {
            getString(R.string.enable_accessibility)
        }
        
        enableButton.isEnabled = !isEnabled
    }
    
    private fun openAccessibilitySettings() {
        val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
        startActivity(intent)
    }
}