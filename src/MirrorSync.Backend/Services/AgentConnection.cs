using MirrorSync.Backend.Models;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;

namespace MirrorSync.Backend.Services;

public class AgentConnection
{
    private readonly AndroidDevice _device;
    private readonly ILogger _logger;
    private readonly MirrorSyncConfig _config;
    private TcpClient? _tcpClient;
    private NetworkStream? _stream;
    private int _sequenceCounter = 1;
    private int _reconnectAttempts = 0;
    private const int MaxReconnectAttempts = 5;

    public bool IsConnected => _tcpClient?.Connected == true && _device.AgentConnected;

    public AgentConnection(AndroidDevice device, ILogger logger, MirrorSyncConfig config)
    {
        _device = device;
        _logger = logger;
        _config = config;
    }

    public async Task<bool> ConnectAsync()
    {
        try
        {
            _tcpClient = new TcpClient();
            _tcpClient.ReceiveTimeout = 5000;
            _tcpClient.SendTimeout = 5000;
            
            await _tcpClient.ConnectAsync(_config.AgentHost, _config.AgentPort);
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

    public async Task<ScreenshotData?> GetScreenshotAsync()
    {
        if (_stream == null || !_device.AgentConnected)
            return null;

        try
        {
            var screenshotCommand = new { type = "SCREENSHOT" };
            var json = JsonSerializer.Serialize(screenshotCommand);
            var data = Encoding.UTF8.GetBytes(json + "\n");
            
            await _stream.WriteAsync(data);

            // Протокол: 4 байта size (big-endian), 4 width, 4 height, затем JPEG
            var header = new byte[12];
            var headerRead = 0;
            while (headerRead < 12)
            {
                var n = await _stream.ReadAsync(header, headerRead, 12 - headerRead);
                if (n == 0) return null;
                headerRead += n;
            }
            var size = ReadInt32BigEndian(header.AsSpan(0, 4));
            var width = ReadInt32BigEndian(header.AsSpan(4, 4));
            var height = ReadInt32BigEndian(header.AsSpan(8, 4));

            if (size <= 0 || size > 10 * 1024 * 1024) // Максимум 10MB
                return null;

            var imageData = new byte[size];
            var totalRead = 0;
            while (totalRead < size)
            {
                var n = await _stream.ReadAsync(imageData, totalRead, size - totalRead);
                if (n == 0) break;
                totalRead += n;
            }

            if (totalRead == size)
            {
                return new ScreenshotData
                {
                    Data = imageData,
                    Width = width,
                    Height = height
                };
            }

            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError("Screenshot failed for {Serial}: {Error}", _device.Serial, ex.Message);
            return null;
        }
    }

    private static int ReadInt32BigEndian(ReadOnlySpan<byte> span)
    {
        return (span[0] << 24) | (span[1] << 16) | (span[2] << 8) | span[3];
    }
}