using MirrorSync.Backend.Services;
using Serilog;

var builder = WebApplication.CreateBuilder(args);

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .WriteTo.Console()
    .WriteTo.File("logs/mirrorsync-.txt", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

// Add Windows Service support
if (args.Contains("--service"))
{
    builder.Host.UseWindowsService();
}

// Add services
builder.Services.AddGrpc();
builder.Services.AddSingleton<DeviceManager>();

var app = builder.Build();

// Configure gRPC
app.MapGrpcService<DeviceControlService>();

// Health check endpoint
app.MapGet("/health", () => "OK");

app.Run("http://localhost:50051");