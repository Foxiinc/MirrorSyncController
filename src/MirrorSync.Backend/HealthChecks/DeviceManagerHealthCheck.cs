using Microsoft.Extensions.Diagnostics.HealthChecks;
using MirrorSync.Backend.Services;

namespace MirrorSync.Backend.HealthChecks;

public class DeviceManagerHealthCheck : IHealthCheck
{
    private readonly DeviceManager _deviceManager;

    public DeviceManagerHealthCheck(DeviceManager deviceManager)
    {
        _deviceManager = deviceManager;
    }

    public Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        var devices = _deviceManager.GetAllDevices();
        var connectedDevices = devices.Count(d => d.AgentConnected);
        
        var data = new Dictionary<string, object>
        {
            ["total_devices"] = devices.Count,
            ["connected_devices"] = connectedDevices
        };

        if (devices.Count == 0)
        {
            return Task.FromResult(
                HealthCheckResult.Degraded("No devices connected", data: data));
        }

        return Task.FromResult(
            HealthCheckResult.Healthy($"{connectedDevices}/{devices.Count} devices connected", data: data));
    }
}
