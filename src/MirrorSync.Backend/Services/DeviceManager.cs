using SharpAdbClient;
using MirrorSync.Backend.Models;
using System.Collections.Concurrent;
using System.Diagnostics;

namespace MirrorSync.Backend.Services;

public class DeviceManager
{
    private readonly ConcurrentDictionary<string, AndroidDevice> _devices = new();
    private readonly ConcurrentDictionary<string, AgentConnection> _connections = new();
    private readonly AdbClient _adbClient;
    private readonly ILogger<DeviceManager> _logger;
    private int _nextPort = 4444;
    private DateTime _lastScan = DateTime.MinValue;
    private const int ScanIntervalMs = 5000;

    public DeviceManager(ILogger<DeviceManager> logger)
    {
        _logger = logger;
        _adbClient = new AdbClient();
        
        try
        {
            if (!AdbServer.Instance.GetStatus().IsRunning)
            {
                var adbPath = FindAdbPath();
                if (adbPath != null)
                {
                    var server = new AdbServer();
                    server.StartServer(adbPath, false);
                    _logger.LogInformation("ADB server started");
                }
                else
                {
                    _logger.LogWarning("ADB not found");
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError("Failed to start ADB: {Error}", ex.Message);
        }
    }

    private string? FindAdbPath()
    {
        var paths = new[]
        {
            @"C:\platform-tools\adb.exe",
            @"C:\Android\Sdk\platform-tools\adb.exe",
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), 
                @"Android\Sdk\platform-tools\adb.exe"),
            "adb.exe"
        };

        foreach (var path in paths)
        {
            if (File.Exists(path))
                return path;
        }
        return null;
    }

    public async Task<List<AndroidDevice>> ScanDevicesAsync()
    {
        // Кэширование - не сканируем чаще чем каждые 5 секунд
        if ((DateTime.UtcNow - _lastScan).TotalMilliseconds < ScanIntervalMs)
        {
            return _devices.Values.ToList();
        }

        _lastScan = DateTime.UtcNow;

        try
        {
            var devices = _adbClient.GetDevices();
            var result = new List<AndroidDevice>();

            foreach (var device in devices.Where(d => d.State == DeviceState.Online))
            {
                var androidDevice = _devices.GetOrAdd(device.Serial, serial => new AndroidDevice
                {
                    Serial = serial,
                    Port = _nextPort++,
                    Status = "connected"
                });

                if (string.IsNullOrEmpty(androidDevice.Model))
                {
                    try
                    {
                        var receiver = new ConsoleOutputReceiver();
                        _adbClient.ExecuteRemoteCommand("getprop ro.product.model", device, receiver);
                        androidDevice.Model = receiver.ToString().Trim();
                    }
                    catch
                    {
                        androidDevice.Model = "Unknown";
                    }
                }

                await SetupPortForwardAsync(androidDevice);
                result.Add(androidDevice);
            }

            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError("Error scanning devices: {Error}", ex.Message);
            return _devices.Values.ToList();
        }
    }

    private async Task SetupPortForwardAsync(AndroidDevice device)
    {
        try
        {
            var adbDevice = new DeviceData { Serial = device.Serial };
            
            try
            {
                _adbClient.CreateForward(adbDevice, "tcp:4444", "tcp:4444", false);
            }
            catch (Exception ex)
            {
                _logger.LogWarning("Port forward failed for {Serial}: {Error}", device.Serial, ex.Message);
            }
            
            if (!_connections.ContainsKey(device.Serial))
            {
                var connection = new AgentConnection(device, _logger);
                _connections[device.Serial] = connection;
                await connection.ConnectAsync();
            }
        }
        catch (Exception ex)
        {
            _logger.LogError("Setup port forward failed for {Serial}: {Error}", device.Serial, ex.Message);
        }
    }

    public async Task<bool> SendCommandAsync(DeviceCommand command, List<string> targetDevices)
    {
        var execTime = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() + 50;
        command.ExecTimeDeviceMs = execTime;

        var tasks = new List<Task<bool>>();
        
        foreach (var deviceSerial in targetDevices)
        {
            if (_connections.TryGetValue(deviceSerial, out var connection))
            {
                tasks.Add(connection.SendCommandAsync(command));
            }
        }

        if (tasks.Count == 0) return false;
        
        var results = await Task.WhenAll(tasks);
        return results.All(r => r);
    }

    public AndroidDevice? GetDevice(string serial) => _devices.TryGetValue(serial, out var device) ? device : null;

    public List<AndroidDevice> GetAllDevices() => _devices.Values.ToList();

    public async Task StartMirrorAsync(string serial)
    {
        var device = GetDevice(serial);
        if (device?.MirrorProcess != null) return;

        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = "scrcpy",
                Arguments = $"-s {serial} --window-title=\"Mirror-{serial}\"",
                UseShellExecute = false,
                CreateNoWindow = true
            };

            device!.MirrorProcess = Process.Start(startInfo);
            _logger.LogInformation("Mirror started for {Serial}", serial);
        }
        catch (Exception ex)
        {
            _logger.LogError("Mirror failed for {Serial}: {Error}", serial, ex.Message);
        }
        
        await Task.CompletedTask;
    }

    public void StopMirror(string serial)
    {
        var device = GetDevice(serial);
        if (device?.MirrorProcess != null)
        {
            try
            {
                device.MirrorProcess.Kill();
            }
            catch { }
            device.MirrorProcess = null;
            _logger.LogInformation("Mirror stopped for {Serial}", serial);
        }
    }
}