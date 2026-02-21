namespace MirrorSync.Backend.Models;

public class ScreenshotData
{
    public byte[] Data { get; set; } = Array.Empty<byte>();
    public int Width { get; set; }
    public int Height { get; set; }
}