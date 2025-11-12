namespace MirrorSync.GUI.Models;

public class DeviceInfo
{
    public string Serial { get; set; } = "";
    public string Model { get; set; } = "";
    public string Status { get; set; } = "";
    public bool AgentConnected { get; set; }
    public int Port { get; set; }
}