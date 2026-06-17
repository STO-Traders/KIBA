; KIBA — Windows installer (Inno Setup 6).
; Compile this on Windows with Inno Setup (https://jrsoftware.org/isdl.php) to produce a
; branded GUI wizard: installer/dist/KIBA-Setup.exe
;
;   1. Install Inno Setup 6 (free).
;   2. Get the KIBA source on the Windows box (clone the repo or copy this folder's parent).
;   3. Open this file in the Inno Setup Compiler and click Build (or run iscc KIBA.iss).
;
; The wizard installs KIBA to the user's profile, runs install.ps1 to set up uv + Python
; 3.11 + the venv + the `kiba` command, and creates Start Menu / Desktop shortcuts.

#define MyAppName "KIBA"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "STO-Traders"
#define MyAppURL "https://github.com/STO-Traders/KIBA"

[Setup]
AppId={{53B443EF-CF5E-487E-A128-851F05AB6886}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={userpf}\KIBA
DefaultGroupName=KIBA
DisableProgramGroupPage=yes
OutputBaseFilename=KIBA-Setup
OutputDir=dist
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=assets\KIBA.ico
WizardImageFile=assets\wizard-large.bmp
WizardSmallImageFile=assets\wizard-small.bmp
UninstallDisplayIcon={app}\installer\assets\KIBA.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
; Bundle the KIBA source tree (parent of this installer dir). Build artifacts, the venv,
; git internals, and the local mac launcher are excluded.
Source: "..\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs; \
    Excludes: "\.git\*,\.venv\*,*.zip,*.pyc,__pycache__\*,installer\dist\*,kiba-trader.command,Kiba.zip"

[Icons]
; These resolve once install.ps1 has created the kiba.exe entry point.
Name: "{group}\KIBA"; Filename: "{app}\.venv\Scripts\kiba.exe"; \
    Parameters: "--stream"; WorkingDir: "{app}"; IconFilename: "{app}\installer\assets\KIBA.ico"
Name: "{userdesktop}\KIBA"; Filename: "{app}\.venv\Scripts\kiba.exe"; \
    Parameters: "--stream"; WorkingDir: "{app}"; IconFilename: "{app}\installer\assets\KIBA.ico"; Tasks: desktopicon

[Run]
; Set up uv + Python 3.11 + venv + the kiba command (needs internet).
Filename: "powershell.exe"; \
    Parameters: "-ExecutionPolicy Bypass -File ""{app}\install.ps1"""; \
    WorkingDir: "{app}"; StatusMsg: "Installing KIBA (Python, dependencies, kiba command)…"; \
    Flags: waituntilterminated
; Offer to launch after install.
Filename: "{app}\.venv\Scripts\kiba.exe"; Parameters: "--stream"; WorkingDir: "{app}"; \
    Description: "Launch KIBA now"; Flags: postinstall nowait skipifdoesntexist

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.venv"
