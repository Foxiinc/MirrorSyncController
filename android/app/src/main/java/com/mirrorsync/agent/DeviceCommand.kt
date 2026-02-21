package com.mirrorsync.agent

import com.google.gson.annotations.SerializedName

data class DeviceCommand(
    @SerializedName("seq") val sequence: Int,
    @SerializedName("type") val type: String,
    @SerializedName("x") val x: Float,
    @SerializedName("y") val y: Float,
    @SerializedName("end_x") val endX: Float = 0f,
    @SerializedName("end_y") val endY: Float = 0f,
    @SerializedName("duration_ms") val durationMs: Int = 0,
    @SerializedName("text") val text: String? = null,
    @SerializedName("key_code") val keyCode: Int = 0,
    @SerializedName("exec_time_device_ms") val execTimeDeviceMs: Long,
    @SerializedName("tap_view_id") val tapViewId: String? = null,
    @SerializedName("tap_text") val tapText: String? = null,
    @SerializedName("tap_content_desc") val tapContentDesc: String? = null
)

data class DeviceResponse(
    @SerializedName("seq") val sequence: Int,
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String,
    @SerializedName("executed_at_ms") val executedAtMs: Long = System.currentTimeMillis()
)

data class TimeSync(
    @SerializedName("client_time") val clientTime: Long,
    @SerializedName("server_time") val serverTime: Long = System.currentTimeMillis(),
    @SerializedName("round_trip_time") val roundTripTime: Long = 0
)