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
        
        if (!AdbServer.Instance.GetStatus().IsRunning)
        {
            var server = new AdbServer();
            server.StartServer(@"C:\platform-tools\adb.exe", false);
        }
    }

    public async Task<List<AndroidDevice>> ScanDevicesAsync()
    {
        var devices = await _adbClient.GetDevicesAsync();
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
                    await _adbClient.ExecuteRemoteCommandAsync("getprop ro.product.model", device, receiver);
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

    private async Task SetupPortForwardAsync(AndroidDevice device)
    {
        try
        {
            var adbDevice = new DeviceData { Serial = device.Serial };
            await _adbClient.CreateForwardAsync(adbDevice, $"tcp:{device.Port}", "tcp:4444");
            
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