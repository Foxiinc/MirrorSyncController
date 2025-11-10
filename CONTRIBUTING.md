# Contributing to MirrorSync Controller

## Development Setup

### Prerequisites
- Windows 10/11 x64
- .NET 8 SDK
- Python 3.11
- Android SDK with API 24+
- Git

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/MirrorSyncController.git
cd MirrorSyncController
```

2. Install Python dependencies:
```bash
cd gui
pip install -r requirements.txt
cd ..
```

3. Restore .NET packages:
```bash
dotnet restore
```

## Building

Run the build script:
```cmd
build.bat
```

## Testing

### Unit Tests
```bash
# Backend tests
cd src\MirrorSync.Backend.Tests
dotnet test

# GUI tests  
cd gui
python -m pytest tests/

# Android tests
cd android
.\gradlew test
```

### System Tests
```bash
python test_system.py
```

## Code Style

- **C#**: Follow Microsoft coding conventions
- **Python**: Follow PEP 8
- **Kotlin**: Follow Android Kotlin style guide

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Reporting Issues

Please use GitHub Issues to report bugs or request features.
Include:
- OS version
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs