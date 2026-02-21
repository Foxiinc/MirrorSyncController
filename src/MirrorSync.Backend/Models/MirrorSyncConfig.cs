namespace MirrorSync.Backend.Models;

public class MirrorSyncConfig
{
    public int GrpcPort { get; set; } = 50051;
    public string AgentHost { get; set; } = "127.0.0.1";
    public int AgentPort { get; set; } = 4444;
    public int MaxDevices { get; set; } = 20;
    public int ScanIntervalMs { get; set; } = 5000;
    public int CommandTimeoutMs { get; set; } = 5000;
    public int SyncDelayMs { get; set; } = 50;
    public int MaxReconnectAttempts { get; set; } = 5;
    public List<string> AdbPaths { get; set; } = new();
}
