using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Grpc.Net.Client;
using MirrorSync.GUI.Models;
using MirrorSync.Protos;

namespace MirrorSync.GUI.Services;

public class BackendService
{
    private readonly GrpcChannel _channel;
    private readonly DeviceControl.DeviceControlClient _client;
    
    public BackendService()
    {
        _channel = GrpcChannel.ForAddress("http://localhost:50051");
        _client = new DeviceControl.DeviceControlClient(_channel);
    }
    
    public async Task<List<DeviceInfo>> GetDevicesAsync()
    {
        try
        {
            var response = await _client.ListDevicesAsync(new Empty());
            return response.Devices.Select(d => new DeviceInfo
            {
                Serial = d.Serial,
                Model = d.Model,
                Status = d.Status,
                AgentConnected = d.AgentConnected,
                Port = d.Port
            }).ToList();
        }
        catch
        {
            return new List<DeviceInfo>();
        }
    }
    
    public async Task<bool> SendCommandAsync(string type, double x, double y, 
        double endX = 0, double endY = 0, string[]? targetDevices = null)
    {
        try
        {
            var request = new CommandRequest
            {
                Type = type,
                X = (float)x,
                Y = (float)y,
                EndX = (float)endX,
                EndY = (float)endY
            };
            
            if (targetDevices != null)
            {
                request.TargetDevices.AddRange(targetDevices);
            }
            
            var response = await _client.SendCommandAsync(request);
            return response.Success;
        }
        catch
        {
            return false;
        }
    }
    
    public async Task<bool> SendTextAsync(string text, string[]? targetDevices = null)
    {
        try
        {
            var request = new CommandRequest
            {
                Type = "TEXT",
                Text = text
            };
            
            if (targetDevices != null)
            {
                request.TargetDevices.AddRange(targetDevices);
            }
            
            var response = await _client.SendCommandAsync(request);
            return response.Success;
        }
        catch
        {
            return false;
        }
    }
    
    public async Task<bool> StartMirrorAsync(string serial)
    {
        try
        {
            var request = new MirrorRequest { Serial = serial };
            var response = await _client.StartMirrorAsync(request);
            return response.Success;
        }
        catch
        {
            return false;
        }
    }
    
    public async Task<bool> StopMirrorAsync(string serial)
    {
        try
        {
            var request = new MirrorRequest { Serial = serial };
            var response = await _client.StopMirrorAsync(request);
            return response.Success;
        }
        catch
        {
            return false;
        }
    }
    
    public void Dispose()
    {
        _channel?.Dispose();
    }
}