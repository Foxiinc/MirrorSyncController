using System.Collections.Concurrent;
using MirrorSync.Backend.Models;

namespace MirrorSync.Backend.Services;

public class ConnectionPool : IDisposable
{
    private readonly ConcurrentDictionary<string, AgentConnection> _connections = new();
    private readonly ILogger<ConnectionPool> _logger;
    private readonly SemaphoreSlim _semaphore = new(20);

    public ConnectionPool(ILogger<ConnectionPool> logger)
    {
        _logger = logger;
    }

    public async Task<AgentConnection?> GetOrCreateConnectionAsync(AndroidDevice device)
    {
        if (_connections.TryGetValue(device.Serial, out var existingConnection))
        {
            if (existingConnection.IsConnected)
                return existingConnection;
            
            _connections.TryRemove(device.Serial, out _);
        }

        await _semaphore.WaitAsync();
        try
        {
            var connection = new AgentConnection(device, _logger);
            if (await connection.ConnectAsync())
            {
                _connections[device.Serial] = connection;
                return connection;
            }
            return null;
        }
        finally
        {
            _semaphore.Release();
        }
    }

    public void RemoveConnection(string serial)
    {
        if (_connections.TryRemove(serial, out var connection))
        {
            connection.Disconnect();
        }
    }

    public void Dispose()
    {
        foreach (var connection in _connections.Values)
        {
            connection.Disconnect();
        }
        _connections.Clear();
        _semaphore.Dispose();
    }
}
