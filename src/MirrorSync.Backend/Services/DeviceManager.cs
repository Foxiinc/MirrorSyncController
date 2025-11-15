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

    public DeviceManager(ILogger<DeviceManager> logger)
    {
        _logger = logger;
        _adbClient = new AdbClient();
        
        try
        {
            // Попробуем найти ADB в разных местах
            var adbPaths = new[]
            {
                @"C:\platform-tools\adb.exe",
                @"C:\Android\Sdk\platform-tools\adb.exe",
                @"C:\Users\" + Environment.UserName + @"\AppData\Local\Android\Sdk\platform-tools\adb.exe",
                "adb.exe", // В PATH
                "adb" // Linux/Mac
            };
            
            string? workingAdbPath = null;
            foreach (var path in adbPaths)
            {
                if (File.Exists(path) || path.Contains("adb") && !path.Contains(@"C:\"))
                {
                    workingAdbPath = path;
                    break;
                }
            }
            
            if (workingAdbPath == null)
            {
                _logger.LogWarning("ADB not found. Please install Android SDK Platform Tools.");
                return;
            }
            
            if (!AdbServer.Instance.GetStatus().IsRunning)
            {
                var server = new AdbServer();
                server.StartServer(workingAdbPath, false);
                _logger.LogInformation("ADB server started with path: {Path}", workingAdbPath);
            }
            else
            {
                _logger.LogInformation("ADB server already running");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError("Failed to start ADB server: {Error}", ex.Message);
            _logger.LogWarning("Device management will be limited without ADB");
        }
    }

    public async Task<List<AndroidDevice>> ScanDevicesAsync()
    {
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
                    catch (Exception ex)
                    {
                        _logger.LogWarning("Failed to get model for {Serial}: {Error}", device.Serial, ex.Message);
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
            return new List<AndroidDevice>();
        }
    }

    private async Task SetupPortForwardAsync(AndroidDevice device)
    {
        try
        {
            var adbDevice = new DeviceData { Serial = device.Serial };
            
            // Настраиваем port forwarding
            try
            {
                // Простое port forwarding на фиксированный порт
                _adbClient.CreateForward(adbDevice, "tcp:4444", "tcp:4444", false);
                _logger.LogInformation("Port forwarding setup: {LocalPort} -> {DevicePort} for {Serial}", 
                    device.Port, 4444, device.Serial);
            }
            catch (Exception ex)
            {
                _logger.LogWarning("Failed to create port forward for {Serial}: {Error}", device.Serial, ex.Message);
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
            _logger.LogError("Failed to setup port forward for {Serial}: {Error}", device.Serial, ex.Message);
        }
    }

    public async Task<bool> SendCommandAsync(DeviceCommand command, List<string> targetDevices)
    {
        var execTime = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() + 50; // 50ms delay
        command.ExecTimeDeviceMs = execTime;

        var tasks = new List<Task<bool>>();
        
        foreach (var deviceSerial in targetDevices)
        {
            if (_connections.TryGetValue(deviceSerial, out var connection))
            {
                tasks.Add(connection.SendCommandAsync(command));
            }
        }

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
            _logger.LogInformation("Started mirror for device {Serial}", serial);
        }
        catch (Exception ex)
        {
            _logger.LogError("Failed to start mirror for {Serial}: {Error}", serial, ex.Message);
        }
        
        await Task.CompletedTask;
    }

    public void StopMirror(string serial)
    {
        var device = GetDevice(serial);
        if (device?.MirrorProcess != null)
        {
            device.MirrorProcess.Kill();
            device.MirrorProcess = null;
            _logger.LogInformation("Stopped mirror for device {Serial}", serial);
        }
    }
}