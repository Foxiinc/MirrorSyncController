using MirrorSync.Backend.Models;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;

namespace MirrorSync.Backend.Services;

public class AgentConnection
{
    private readonly AndroidDevice _device;
    private readonly ILogger _logger;
    private TcpClient? _tcpClient;
    private NetworkStream? _stream;
    private int _sequenceCounter = 1;

    public AgentConnection(AndroidDevice device, ILogger logger)
    {
        _device = device;
        _logger = logger;
    }

    public async Task<bool> ConnectAsync()
    {
        try
        {
            _tcpClient = new TcpClient();
            await _tcpClient.ConnectAsync("127.0.0.1", _device.Port);
            _stream = _tcpClient.GetStream();
            
            await SyncTimeAsync();
            _device.AgentConnected = true;
            _device.LastPingMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            
            _logger.LogInformation("Connected to agent on device {Serial}", _device.Serial);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError("Failed to connect to agent on {Serial}: {Error}", _device.Serial, ex.Message);
            _device.AgentConnected = false;
            return false;
        }
    }

    private async Task SyncTimeAsync()
    {
        var syncCommand = new
        {
            type = "TIME_SYNC",
            client_time = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
        };

        var json = JsonSerializer.Serialize(syncCommand);
        var data = Encoding.UTF8.GetBytes(json + "\n");
        
        await _stream!.WriteAsync(data);
        
        var buffer = new byte[1024];
        var bytesRead = await _stream.ReadAsync(buffer);
        var response = Encoding.UTF8.GetString(buffer, 0, bytesRead);
        
        var timeSync = JsonSerializer.Deserialize<TimeSync>(response);
        if (timeSync != null)
        {
            _device.TimeOffsetMs = timeSync.Offset;
            _logger.LogDebug("Time sync completed for {Serial}, offset: {Offset}ms", _device.Serial, _device.TimeOffsetMs);
        }
    }

    public async Task<bool> SendCommandAsync(DeviceCommand command)
    {
        if (_stream == null || !_device.AgentConnected)
        {
            return false;
        }

        try
        {
            command.Sequence = _sequenceCounter++;
            command.ExecTimeDeviceMs += _device.TimeOffsetMs;

            var json = JsonSerializer.Serialize(command);
            var data = Encoding.UTF8.GetBytes(json + "\n");
            
            await _stream.WriteAsync(data);
            
            var buffer = new byte[1024];
            var bytesRead = await _stream.ReadAsync(buffer);
            var response = Encoding.UTF8.GetString(buffer, 0, bytesRead);
            
            var deviceResponse = JsonSerializer.Deserialize<DeviceResponse>(response);
            return deviceResponse?.Success ?? false;
        }
        catch (Exception ex)
        {
            _logger.LogError("Failed to send command to {Serial}: {Error}", _device.Serial, ex.Message);
            _device.AgentConnected = false;
            return false;
        }
    }

    public void Disconnect()
    {
        _stream?.Close();
        _tcpClient?.Close();
        _device.AgentConnected = false;
    }
}