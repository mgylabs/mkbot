; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

; #define NameLong "Mulgyeol MK Bot OSS"
; #define NameShort "MK Bot"
; #define Version "3.5.7"
; #define AppExeName "MKBot.exe"
; #define AppMutex "MKBotOSS"
; #define ExtDirName ".mkbot-oss"
; #define DName "mkbot"
#define RepoDir ".."

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={#NameLong}
AppName={#NameLong}
AppVersion={#Version}
AppVerName={#NameLong}
AppPublisher=Mulgyeol Labs
AppPublisherURL=https://github.com/mgylabs/mkbot
AppSupportURL=https://github.com/mgylabs/mkbot
AppUpdatesURL=https://github.com/mgylabs/mkbot
DefaultGroupName={#NameShort}
DefaultDirName={userpf}\{#NameLong}
DisableDirPage=yes
DisableProgramGroupPage=yes
LicenseFile={#RepoDir}\LICENSE
; Remove the following line to run in administrative install mode (install for all users.)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline
OutputDir={#RepoDir}
OutputBaseFilename=MKBotSetup-{#Version}
SetupIconFile={#RepoDir}\resources\package\mkbot.ico
WizardImageFile={#RepoDir}\resources\package\welcome.bmp
WizardSmallImageFile={#RepoDir}\resources\package\mkbot_sq.bmp
UninstallDisplayIcon={app}\{#AppExeName}
ChangesAssociations=true
Compression=lzma/ultra
SolidCompression=yes
AppMutex={code:GetAppMutex}
SetupMutex={#AppMutex}setup
ShowLanguageDialog=auto
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "korean"; MessagesFile: "{#RepoDir}\package\i18n\Korean.isl"

; [InstallDelete]
; Type: filesandordirs; Name: "{autoprograms}\{#NameLong}";

; [UninstallDelete]
; Type: filesandordirs; Name: "{app}"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";
Name: "runapp"; Description: "{cm:LaunchProgram,{#NameShort}}"; GroupDescription: "{cm:LaunchProgram}"; Check: WizardSilent

[Files]
Source: "{#RepoDir}\build\*"; DestDir: "{code:GetDestDir}"; Flags: ignoreversion
Source: "{#RepoDir}\build\bin\*"; DestDir: "{code:GetDestDir}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#RepoDir}\package\info\*"; DestDir: "{code:GetDestDir}\info"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#RepoDir}\resources\app\*"; DestDir: "{code:GetDestDir}\resources\app"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#RepoDir}\resources\common\*"; DestDir: "{code:GetDestDir}\resources\common"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#RepoDir}\resources\*"; DestDir: "{code:GetDestDir}"; Flags: ignoreversion
Source: "{#RepoDir}\locales\*.mo"; DestDir: "{code:GetDestDir}\bin\locales"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#RepoDir}\package\tools\Update.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#RepoDir}\package\data\*"; DestDir: "{localappdata}\Mulgyeol\{#NameLong}\data"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist uninsneveruninstall
Source: "{#RepoDir}\extensions\*"; DestDir: "{%USERPROFILE}\{#ExtDirName}\extensions"; Flags: ignoreversion recursesubdirs createallsubdirs uninsneveruninstall
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#NameShort}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; AppUserModelToastActivatorCLSID: "3f7eb835-ef29-45f5-acb5-a078d127dc94"; AppUserModelID: "com.mgylabs.{#DName}";
Name: "{autodesktop}\{#NameShort}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#AppExeName}"; Parameters: "--post-update"; Description: "{cm:LaunchProgram,{#NameLong}}"; Tasks: runapp; Flags: nowait postinstall; Check: ShouldRunAfterUpdate
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(NameLong, '&', '&&')}}"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#NameLong}"; ValueData: "{app}\{#AppExeName}"; Flags: deletevalue uninsdeletevalue;

[Code]
function WizardNotSilent(): Boolean;
begin
  Result := not WizardSilent();
end;

// Updates
function IsBackgroundUpdate(): Boolean;
begin
  Result := ExpandConstant('{param:update|false}') <> 'false';
end;

function NeedUpdaterGUI(): Boolean;
begin
  Result := ExpandConstant('{param:gui|true}') = 'true';
end;

function IsNotUpdate(): Boolean;
begin
  Result := not IsBackgroundUpdate();
end;

function LockFileExists(): Boolean;
begin
  Result := FileExists(ExpandConstant('{param:update}'))
end;

function ShouldRunAfterUpdate(): Boolean;
begin
  if IsBackgroundUpdate() then
    Result := not LockFileExists()
  else
    Result := True;
end;

function GetAppMutex(Value: string): string;
begin
  if IsBackgroundUpdate() then
    Result := ''
  else
    Result := '{#AppMutex}';
end;

function GetDestDir(Value: string): string;
begin
  if IsBackgroundUpdate() then
    Result := ExpandConstant('{app}\_')
  else
    Result := ExpandConstant('{app}');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  UpdateResultCode: Integer;
  Args_GUI: String;
  Args_AutoRun: String;
begin
  if IsBackgroundUpdate() and (CurStep = ssPostInstall) then
  begin
    CreateMutex('{#AppMutex}-ready');

    while (CheckForMutexes('{#AppMutex}')) do
    begin
      Log('Application is still running, waiting');
      Sleep(1000);
    end;

    Args_GUI := ''
    Args_AutoRun := ''

    if NeedUpdaterGUI() then
    begin
        Args_GUI := ' --gui'
    end;

    if ShouldRunAfterUpdate() then
    begin
        Args_AutoRun := ' --auto-run'
    end;

    Exec(ExpandConstant('{app}\Update.exe'), ExpandConstant('"bin\{#AppExeName}" "{#NameLong}" "{#DName}" --start -rb' + Args_GUI + Args_AutoRun), '', SW_SHOW, ewWaitUntilTerminated, UpdateResultCode);
  end;
end;
