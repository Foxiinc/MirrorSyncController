using System;
using System.Collections.ObjectModel;
using System.Reactive;
using System.Reactive.Linq;
using System.Threading.Tasks;
using ReactiveUI;
using Avalonia.Media.Imaging;
using MirrorSync.GUI.Services;
using MirrorSync.GUI.Models;

namespace MirrorSync.GUI.ViewModels;

public class MainWindowViewModel : ViewModelBase
{
    private readonly BackendService _backendService;
    private readonly MirrorService _mirrorService;
    
    public ObservableCollection<DeviceInfo> Devices { get; } = new();
    
    private DeviceInfo? _selectedDevice;
    public DeviceInfo? SelectedDevice
    {
        get => _selectedDevice;
        set => this.RaiseAndSetIfChanged(ref _selectedDevice, value);
    }
    
    private bool _isBroadcastMode;
    public bool IsBroadcastMode
    {
        get => _isBroadcastMode;
        set => this.RaiseAndSetIfChanged(ref _isBroadcastMode, value);
    }
    
    private string _inputText = "";
    public string InputText
    {
        get => _inputText;
        set => this.RaiseAndSetIfChanged(ref _inputText, value);
    }
    
    private Bitmap? _mirrorImage;
    public Bitmap? MirrorImage
    {
        get => _mirrorImage;
        set => this.RaiseAndSetIfChanged(ref _mirrorImage, value);
    }
    
    public ReactiveCommand<Unit, Unit> RefreshDevicesCommand { get; }
    public ReactiveCommand<Unit, Unit> TapCommand { get; }
    public ReactiveCommand<Unit, Unit> SwipeCommand { get; }
    public ReactiveCommand<Unit, Unit> SendTextCommand { get; }
    public ReactiveCommand<Unit, Unit> StartMirrorCommand { get; }
    public ReactiveCommand<Unit, Unit> StopMirrorCommand { get; }
    
    public MainWindowViewModel()
    {
        _backendService = new BackendService();
        _mirrorService = new MirrorService();
        
        RefreshDevicesCommand = ReactiveCommand.CreateFromTask(RefreshDevices);
        TapCommand = ReactiveCommand.CreateFromTask(SendTap);
        SwipeCommand = ReactiveCommand.CreateFromTask(SendSwipe);
        SendTextCommand = ReactiveCommand.CreateFromTask(SendText);
        StartMirrorCommand = ReactiveCommand.CreateFromTask(StartMirror);
        StopMirrorCommand = ReactiveCommand.CreateFromTask(StopMirror);
        
        // Auto-refresh devices every 5 seconds
        Observable.Timer(TimeSpan.Zero, TimeSpan.FromSeconds(5))
            .Subscribe(_ => RefreshDevicesCommand.Execute().Subscribe());
            
        // Subscribe to mirror updates
        _mirrorService.MirrorImageUpdated
            .ObserveOn(RxApp.MainThreadScheduler)
            .Subscribe(image => MirrorImage = image);
    }
    
    private async Task RefreshDevices()
    {
        try
        {
            var devices = await _backendService.GetDevicesAsync();
            Devices.Clear();
            foreach (var device in devices)
            {
                Devices.Add(device);
            }
        }
        catch (Exception ex)
        {
            // Log error
            Console.WriteLine($"Error refreshing devices: {ex.Message}");
        }
    }
    
    private async Task SendTap()
    {
        if (SelectedDevice == null && !IsBroadcastMode) return;
        
        var targets = IsBroadcastMode ? null : new[] { SelectedDevice!.Serial };
        await _backendService.SendCommandAsync("TAP", 0.5, 0.5, 0, 0, targets);
    }
    
    public async void HandleTapAt(double x, double y)
    {
        if (SelectedDevice == null && !IsBroadcastMode) return;
        
        var targets = IsBroadcastMode ? null : new[] { SelectedDevice!.Serial };
        await _backendService.SendCommandAsync("TAP", x, y, 0, 0, targets);
    }
    
    private async Task SendSwipe()
    {
        if (SelectedDevice == null && !IsBroadcastMode) return;
        
        await _backendService.SendCommandAsync("SWIPE", 0.2, 0.5, 0.8, 0.5,
            IsBroadcastMode ? null : new[] { SelectedDevice!.Serial });
    }
    
    private async Task SendText()
    {
        if (string.IsNullOrEmpty(InputText) || (SelectedDevice == null && !IsBroadcastMode)) return;
        
        await _backendService.SendTextAsync(InputText,
            IsBroadcastMode ? null : new[] { SelectedDevice!.Serial });
        
        InputText = "";
    }
    
    private async Task StartMirror()
    {
        if (SelectedDevice == null) return;
        
        await _backendService.StartMirrorAsync(SelectedDevice.Serial);
        _mirrorService.StartMirror(SelectedDevice.Serial);
    }
    
    private async Task StopMirror()
    {
        if (SelectedDevice == null) return;
        
        await _backendService.StopMirrorAsync(SelectedDevice.Serial);
        _mirrorService.StopMirror();
    }
}