using Grpc.Core;
using Google.Rpc;
using Google.Protobuf.WellKnownTypes;
using MirrorSync.Protos;
using MirrorSync.Backend.Models;
using ProtoEmpty = MirrorSync.Protos.Empty;

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

    public override async Task<DeviceList> ListDevices(ProtoEmpty request, ServerCallContext context)
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
            KeyCode = request.KeyCode,
            TapViewId = request.TapViewId,
            TapText = request.TapText,
            TapContentDesc = request.TapContentDesc
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
            var device = _deviceManager.GetDevice(request.Serial);
            if (device == null)
            {
                throw new Google.Rpc.Status
                {
                    Code = (int)Code.NotFound,
                    Message = "Device not found",
                    Details =
                    {
                        Any.Pack(new BadRequest
                        {
                            FieldViolations =
                            {
                                new BadRequest.Types.FieldViolation
                                {
                                    Field = "serial",
                                    Description = $"Device with serial '{request.Serial}' not found"
                                }
                            }
                        })
                    }
                }.ToRpcException();
            }

            await _deviceManager.StartMirrorAsync(request.Serial);
            return new MirrorResponse { Success = true, Message = "Mirror started" };
        }
        catch (RpcException)
        {
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to start mirror for {Serial}", request.Serial);
            throw new Google.Rpc.Status
            {
                Code = (int)Code.Internal,
                Message = "Internal error starting mirror",
                Details =
                {
                    Any.Pack(new ErrorInfo
                    {
                        Reason = "MIRROR_START_FAILED",
                        Domain = "mirrorsync.backend",
                        Metadata = { ["serial"] = request.Serial }
                    })
                }
            }.ToRpcException();
        }
    }

    public override Task<MirrorResponse> StopMirror(MirrorRequest request, ServerCallContext context)
    {
        try
        {
            var device = _deviceManager.GetDevice(request.Serial);
            if (device == null)
            {
                throw new Google.Rpc.Status
                {
                    Code = (int)Code.NotFound,
                    Message = "Device not found"
                }.ToRpcException();
            }

            _deviceManager.StopMirror(request.Serial);
            return Task.FromResult(new MirrorResponse { Success = true, Message = "Mirror stopped" });
        }
        catch (RpcException)
        {
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to stop mirror for {Serial}", request.Serial);
            throw new Google.Rpc.Status
            {
                Code = (int)Code.Internal,
                Message = "Internal error stopping mirror"
            }.ToRpcException();
        }
    }

    public override async Task<ScreenshotResponse> GetScreenshot(ScreenshotRequest request, ServerCallContext context)
    {
        try
        {
            var device = _deviceManager.GetDevice(request.Serial);
            if (device == null)
            {
                return new ScreenshotResponse { Success = false };
            }

            var screenshotData = await _deviceManager.GetScreenshotAsync(request.Serial);
            if (screenshotData != null)
            {
                return new ScreenshotResponse
                {
                    Success = true,
                    ImageData = Google.Protobuf.ByteString.CopyFrom(screenshotData.Data),
                    Width = screenshotData.Width,
                    Height = screenshotData.Height
                };
            }

            return new ScreenshotResponse { Success = false };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get screenshot for {Serial}", request.Serial);
            return new ScreenshotResponse { Success = false };
        }
    }
}