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
    private int _reconnectAttempts = 0;
    private const int MaxReconnectAttempts = 5;

    public bool IsConnected => _tcpClient?.Connected == true && _device.AgentConnected;

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
            _tcpClient.ReceiveTimeout = 5000;
            _tcpClient.SendTimeout = 5000;
            
            // Подключаемся к порту 4444 (фиксированный порт агента)
            await _tcpClient.ConnectAsync("127.0.0.1", 4444);
            _stream = _tcpClient.GetStream();
            
            // Проверяем соединение пингом
            var pingCommand = new { type = "PING" };
            var json = JsonSerializer.Serialize(pingCommand);
            var data = Encoding.UTF8.GetBytes(json + "\n");
            await _stream.WriteAsync(data);
            
            var buffer = new byte[1024];
            var bytesRead = await _stream.ReadAsync(buffer);
            
            if (bytesRead > 0)
            {
                await SyncTimeAsync();
                _device.AgentConnected = true;
                _device.LastPingMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                
                _logger.LogInformation("Connected to agent on device {Serial} port {Port}", _device.Serial, _device.Port);
                return true;
            }
            
            throw new Exception("No response from agent");
        }
        catch (Exception ex)
        {
            _logger.LogWarning("Failed to connect to agent on {Serial}:{Port} - {Error}", _device.Serial, _device.Port, ex.Message);
            _device.AgentConnected = false;
            Disconnect();
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
            if (_reconnectAttempts < MaxReconnectAttempts)
            {
                _reconnectAttempts++;
                var delay = Math.Min(1000 * (int)Math.Pow(2, _reconnectAttempts), 30000);
                _logger.LogWarning("Attempting reconnect {Attempt}/{Max} after {Delay}ms for {Serial}", 
                    _reconnectAttempts, MaxReconnectAttempts, delay, _device.Serial);
                
                await Task.Delay(delay);
                
                if (await ConnectAsync())
                {
                    _reconnectAttempts = 0;
                    return await SendCommandAsync(command);
                }
            }
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
            _reconnectAttempts = 0; // Сброс счетчика при успехе
            return deviceResponse?.Success ?? false;
        }
        catch (Exception ex)
        {
            _logger.LogError("Failed to send command to {Serial}: {Error}", _device.Serial, ex.Message);
            _device.AgentConnected = false;
            Disconnect();
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