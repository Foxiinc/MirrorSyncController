using Avalonia.Controls;
using Avalonia.Input;
using MirrorSync.GUI.ViewModels;

namespace MirrorSync.GUI.Views;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        
        // Handle mouse clicks on mirror image for tap commands
        var mirrorImage = this.FindControl<Avalonia.Controls.Image>("MirrorImage");
        if (mirrorImage != null)
        {
            mirrorImage.PointerPressed += OnMirrorImageClick;
        }
    }

    private void OnMirrorImageClick(object? sender, PointerPressedEventArgs e)
    {
        if (DataContext is MainWindowViewModel vm && sender is Avalonia.Controls.Image image)
        {
            var position = e.GetPosition(image);
            var normalizedX = position.X / image.Bounds.Width;
            var normalizedY = position.Y / image.Bounds.Height;
            
            vm.HandleTapAt(normalizedX, normalizedY);
        }
    }
}