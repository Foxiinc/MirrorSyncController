using System;
using System.Diagnostics;
using System.Reactive.Subjects;
using System.Threading.Tasks;
using Avalonia.Media.Imaging;

namespace MirrorSync.GUI.Services;

public class MirrorService
{
    private Process? _scrcpyProcess;
    private readonly Subject<Bitmap?> _mirrorImageSubject = new();
    
    public IObservable<Bitmap?> MirrorImageUpdated => _mirrorImageSubject;
    
    public void StartMirror(string deviceSerial)
    {
        StopMirror();
        
        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = "scrcpy",
                Arguments = $"-s {deviceSerial} --no-audio --stay-awake",
                UseShellExecute = false,
                CreateNoWindow = true
            };
            
            _scrcpyProcess = Process.Start(startInfo);
            
            // TODO: Capture scrcpy output and convert to bitmap
            // For now, just show a placeholder
            Task.Run(async () =>
            {
                await Task.Delay(2000);
                // Create a simple placeholder bitmap
                var bitmap = CreatePlaceholderBitmap();
                _mirrorImageSubject.OnNext(bitmap);
            });
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to start scrcpy: {ex.Message}");
        }
    }
    
    public void StopMirror()
    {
        try
        {
            _scrcpyProcess?.Kill();
            _scrcpyProcess?.Dispose();
            _scrcpyProcess = null;
            _mirrorImageSubject.OnNext(null);
        }
        catch
        {
            // Ignore errors when stopping
        }
    }
    
    private Bitmap CreatePlaceholderBitmap()
    {
        // Create a simple 400x800 placeholder bitmap
        var width = 400;
        var height = 800;
        var bitmap = new WriteableBitmap(new Avalonia.PixelSize(width, height), 
            new Avalonia.Vector(96, 96), Avalonia.Platform.PixelFormat.Bgra8888);
        
        // Simple placeholder - return empty bitmap
        // TODO: Implement proper bitmap creation
        
        return bitmap;
    }
    
    public void Dispose()
    {
        StopMirror();
        _mirrorImageSubject.Dispose();
    }
}