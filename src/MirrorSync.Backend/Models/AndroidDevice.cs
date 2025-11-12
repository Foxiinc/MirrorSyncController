using System.Diagnostics;

namespace MirrorSync.Backend.Models;

public class AndroidDevice
{
    public string Serial { get; set; } = string.Empty;
    public string Model { get; set; } = string.Empty;
    public string Status { get; set; } = "disconnected";
    public bool AgentConnected { get; set; }
    public int Port { get; set; }
    public long TimeOffsetMs { get; set; }
    public long LastPingMs { get; set; }
    public Process? MirrorProcess { get; set; }
}

public class TimeSync
{
    public long ClientTime { get; set; }
    public long ServerTime { get; set; }
    public long RoundTripTime { get; set; }
    public long Offset => ServerTime - ClientTime - (RoundTripTime / 2);
}