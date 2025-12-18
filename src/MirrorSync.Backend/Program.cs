using MirrorSync.Backend.Services;
using MirrorSync.Backend.Models;
using Serilog;

var builder = WebApplication.CreateBuilder(args);

// Create logs directory
var logsDir = Path.Combine(AppContext.BaseDirectory, "logs");
Directory.CreateDirectory(logsDir);

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .WriteTo.Console()
    .WriteTo.File(Path.Combine(logsDir, "mirrorsync-.txt"), rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

// Add Windows Service support
if (args.Contains("--service"))
{
    builder.Host.UseWindowsService();
}

// Configure settings
var config = builder.Configuration.GetSection("MirrorSync").Get<MirrorSyncConfig>() ?? new MirrorSyncConfig();

// Configure Kestrel for gRPC
builder.WebHost.ConfigureKestrel(options =>
{
    options.ListenLocalhost(config.GrpcPort, o => o.Protocols = Microsoft.AspNetCore.Server.Kestrel.Core.HttpProtocols.Http2);
});
builder.Services.AddSingleton(config);

// Add services
builder.Services.AddGrpc();
builder.Services.AddHealthChecks()
    .AddCheck<MirrorSync.Backend.HealthChecks.DeviceManagerHealthCheck>("device_manager");
builder.Services.AddSingleton<ConnectionPool>();
builder.Services.AddSingleton<DeviceManager>();

var app = builder.Build();

// Configure gRPC
app.MapGrpcService<DeviceControlService>();

// Health check endpoint
app.MapHealthChecks("/health");

Log.Information("MirrorSync Backend starting on port 50051");
app.Run();