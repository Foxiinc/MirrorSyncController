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

// Configure Kestrel for gRPC
builder.WebHost.ConfigureKestrel(options =>
{
    options.ListenLocalhost(50051, o => o.Protocols = Microsoft.AspNetCore.Server.Kestrel.Core.HttpProtocols.Http2);
});

// Add services
builder.Services.AddGrpc();
builder.Services.AddSingleton<DeviceManager>();

var app = builder.Build();

// Configure gRPC
app.MapGrpcService<DeviceControlService>();

// Health check endpoint
app.MapGet("/health", () => "OK");

app.Run();