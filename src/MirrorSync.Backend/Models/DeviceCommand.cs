using System.Text.Json.Serialization;

namespace MirrorSync.Backend.Models;

public class DeviceCommand
{
    [JsonPropertyName("seq")]
    public int Sequence { get; set; }

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("x")]
    public float X { get; set; }

    [JsonPropertyName("y")]
    public float Y { get; set; }

    [JsonPropertyName("end_x")]
    public float EndX { get; set; }

    [JsonPropertyName("end_y")]
    public float EndY { get; set; }

    [JsonPropertyName("duration_ms")]
    public int DurationMs { get; set; }

    [JsonPropertyName("text")]
    public string? Text { get; set; }

    [JsonPropertyName("key_code")]
    public int KeyCode { get; set; }

    [JsonPropertyName("exec_time_device_ms")]
    public long ExecTimeDeviceMs { get; set; }
}

public class DeviceResponse
{
    [JsonPropertyName("seq")]
    public int Sequence { get; set; }

    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    [JsonPropertyName("executed_at_ms")]
    public long ExecutedAtMs { get; set; }
}