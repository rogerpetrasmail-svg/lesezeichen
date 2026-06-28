; Inno Setup Script für den RSS-Rechercheur
; Erzeugt einen klassischen Windows-Installer (Setup.exe) mit Startmenü-
; und optionalem Desktop-Eintrag. Wird im CI auf einem Windows-Runner gebaut.
;
; Erwartet, dass PyInstaller zuvor nach dist\RSS-Rechercheur\ gebaut hat.

#define MyAppName "RSS-Rechercheur"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Lesezeichen"
#define MyAppExeName "RSS-Rechercheur.exe"

[Setup]
AppId={{B7B6F0E2-1A3C-4D58-9F21-RSSRECHERCHEUR01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Quell-Basisverzeichnis ist das Projekt-Stammverzeichnis (eine Ebene über
; packaging/), da PyInstaller seine Ausgabe nach <root>/dist legt. Alle
; relativen Pfade unten beziehen sich dadurch auf den Projekt-Stamm.
SourceDir=..
OutputDir=installer_output
OutputBaseFilename=RSS-Rechercheur-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Gesamten One-Folder-Build übernehmen
Source: "dist\RSS-Rechercheur\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
