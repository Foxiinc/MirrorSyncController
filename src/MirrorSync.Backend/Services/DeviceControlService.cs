using Grpc.Core;
using MirrorSync.Protos;
using MirrorSync.Backend.Models;

namespace MirrorSync.Backend.Services;

public class DeviceControlService : DeviceControl.DeviceControlBase
{
    private readonly DeviceManager _deviceManager;
    private readonly ILogger<DeviceControlService> _logger;

    public DeviceControlService(DeviceManager deviceManager, ILogger<DeviceControlService> logger)
    {
        _deviceManager = deviceManager;
        _logger = logger;
    }

    public override async Task<DeviceList> ListDevices(Empty request, ServerCallContext context)
    {
        var devices = await _deviceManager.ScanDevicesAsync();
        var deviceList = new DeviceList();

        foreach (var device in devices)
        {
            deviceList.Devices.Add(new Device
            {
                Serial = device.Serial,
                Model = device.Model,
                Status = device.Status,
                AgentConnected = device.AgentConnected,
                Port = device.Port
            });
        }

        return deviceList;
    }

    public override async Task<CommandResponse> SendCommand(CommandRequest request, ServerCallContext context)
    {
        var command = new DeviceCommand
        {
            Type = request.Type,
            X = request.X,
            Y = request.Y,
            EndX = request.EndX,
            EndY = request.EndY,
            DurationMs = request.DurationMs,
            Text = request.Text,
            KeyCode = request.KeyCode
        };

        var targetDevices = request.TargetDevices.Count > 0 
            ? request.TargetDevices.ToList() 
            : _deviceManager.GetAllDevices().Select(d => d.Serial).ToList();

        var success = await _deviceManager.SendCommandAsync(command, targetDevices);

        return new CommandResponse
        {
            Success = success,
            Message = success ? "Command sent successfully" : "Failed to send command",
            DevicesCount = targetDevices.Count
        };
    }

    public override Task<DeviceStatusResponse> GetDeviceStatus(DeviceStatusRequest request, ServerCallContext context)
    {
        var device = _deviceManager.GetDevice(request.Serial);
        
        return Task.FromResult(new DeviceStatusResponse
        {
            Serial = request.Serial,
            Status = device?.Status ?? "not_found",
            AgentConnected = device?.AgentConnected ?? false,
            LastPingMs = device?.LastPingMs ?? 0
        });
    }

    public override async Task<MirrorResponse> StartMirror(MirrorRequest request, ServerCallContext context)
    {
        try
        {
            await _deviceManager.StartMirrorAsync(request.Serial);
            return new MirrorResponse { Success = true, Message = "Mirror started" };
        }
        catch (Exception ex)
        {
            return new MirrorResponse { Success = false, Message = ex.Message };
        }
    }

    public override Task<MirrorResponse> StopMirror(MirrorRequest request, ServerCallContext context)
    {
        try
        {
            _deviceManager.StopMirror(request.Serial);
            return Task.FromResult(new MirrorResponse { Success = true, Message = "Mirror stopped" });
        }
        catch (Exception ex)
        {
            return Task.FromResult(new MirrorResponse { Success = false, Message = ex.Message });
        }
    }
}