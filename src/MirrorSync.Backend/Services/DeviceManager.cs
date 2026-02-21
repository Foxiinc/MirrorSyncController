using SharpAdbClient;
using MirrorSync.Backend.Models;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace MirrorSync.Backend.Services;

public class DeviceManager
{
    private readonly ConcurrentDictionary<string, AndroidDevice> _devices = new();
    private readonly ConnectionPool _connectionPool;
    private readonly AdbClient _adbClient;
    private readonly ILogger<DeviceManager> _logger;
    private readonly MirrorSyncConfig _config;
    private DateTime _lastScan = DateTime.MinValue;
    private const int ScanIntervalMs = 5000;

    public DeviceManager(ILogger<DeviceManager> logger, ConnectionPool connectionPool, MirrorSyncConfig config)
    {
        _logger = logger;
        _connectionPool = connectionPool;
        _config = config;
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
        var isWindows = RuntimeInformation.IsOSPlatform(OSPlatform.Windows);
        var adbName = isWindows ? "adb.exe" : "adb";

        if (_config.AdbPaths?.Count > 0)
        {
            foreach (var p in _config.AdbPaths)
            {
                if (!string.IsNullOrWhiteSpace(p) && File.Exists(p))
                    return p;
            }
        }

        var pathEnv = Environment.GetEnvironmentVariable("PATH");
        if (!string.IsNullOrEmpty(pathEnv))
        {
            var separator = isWindows ? ';' : ':';
            foreach (var dir in pathEnv.Split(separator, StringSplitOptions.RemoveEmptyEntries))
            {
                var candidate = Path.Combine(dir.Trim(), adbName);
                if (File.Exists(candidate))
                    return candidate;
            }
        }

        var fallbackPaths = isWindows
            ? new[]
            {
                @"C:\platform-tools\adb.exe",
                @"C:\Android\Sdk\platform-tools\adb.exe",
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    @"Android\Sdk\platform-tools\adb.exe"),
                "adb.exe"
            }
            : new[]
            {
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Android", "Sdk", "platform-tools", "adb"),
                "/usr/bin/adb",
                "/usr/local/bin/adb"
            };

        foreach (var path in fallbackPaths)
        {
            if (!string.IsNullOrEmpty(path) && File.Exists(path))
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
                    Port = _config.AgentPort,
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
            var portStr = _config.AgentPort.ToString();

            try
            {
                _adbClient.CreateForward(adbDevice, $"tcp:{_config.AgentPort}", $"tcp:{portStr}", false);
            }
            catch (Exception ex)
            {
                _logger.LogWarning("Port forward failed for {Serial}: {Error}", device.Serial, ex.Message);
            }

            _ = await _connectionPool.GetOrCreateConnectionAsync(device);
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
            var connection = _connectionPool.GetConnection(deviceSerial);
            if (connection != null)
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
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to kill mirror process for {Serial}", serial);
            }
            device.MirrorProcess = null;
            _logger.LogInformation("Mirror stopped for {Serial}", serial);
        }
    }

    public async Task<ScreenshotData?> GetScreenshotAsync(string serial)
    {
        var connection = _connectionPool.GetConnection(serial);
        if (connection == null)
            return null;

        try
        {
            return await connection.GetScreenshotAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError("Screenshot failed for {Serial}: {Error}", serial, ex.Message);
            return null;
        }
    }
}