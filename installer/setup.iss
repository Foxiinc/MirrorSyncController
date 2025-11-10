[Setup]
AppName=MirrorSync Controller
AppVersion=1.0.0
AppPublisher=MirrorSync Team
DefaultDirName={autopf}\MirrorSync
DefaultGroupName=MirrorSync Controller
OutputDir=Output
OutputBaseFilename=MirrorSyncController-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "service"; Description: "Install Backend as Windows Service"; GroupDescription: "Service Options"; Flags: checkedonce

[Files]
Source: "..\src\MirrorSync.Backend\bin\Release\net8.0\win-x64\publish\*"; DestDir: "{app}\Backend"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\gui\dist\MirrorSyncGUI\*"; DestDir: "{app}\GUI"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\android\app\build\outputs\apk\release\app-release.apk"; DestDir: "{app}\Android"; Flags: ignoreversion
Source: "scrcpy\*"; DestDir: "{app}\Tools\scrcpy"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "platform-tools\*"; DestDir: "{app}\Tools\platform-tools"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\MirrorSync Controller"; Filename: "{app}\GUI\MirrorSyncGUI.exe"
Name: "{group}\{cm:UninstallProgram,MirrorSync Controller}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\MirrorSync Controller"; Filename: "{app}\GUI\MirrorSyncGUI.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Backend\MirrorSync.Backend.exe"; Parameters: "--install-service"; Flags: runhidden; Tasks: service
Filename: "{app}\GUI\MirrorSyncGUI.exe"; Description: "{cm:LaunchProgram,MirrorSync Controller}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\Backend\MirrorSync.Backend.exe"; Parameters: "--uninstall-service"; Flags: runhidden; Tasks: service

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "PATH"; ValueData: "{olddata};{app}\Tools\platform-tools;{app}\Tools\scrcpy"; Check: NeedsAddPath('{app}\Tools\platform-tools') or NeedsAddPath('{app}\Tools\scrcpy')

[Code]
function NeedsAddPath(Param: string): Boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'PATH', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;