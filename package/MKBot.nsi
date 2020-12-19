!define PRODUCT_NAME "Mulgyeol MK Bot"
; !define PRODUCT_VERSION "1.0.0"
!searchreplace PRODUCT_VERSION_NUMBER "${PRODUCT_VERSION}" " Canary" ""
!define PRODUCT_PUBLISHER "Mulgyeol Labs"
!define PRODUCT_WEB_SITE "https://github.com/mgylabs/mulgyeol-mkbot"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\MKBot.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKCU"

Unicode true
RequestExecutionLevel user
; MUI 1.67 compatible ------
!include "FileFunc.nsh"
!include "MUI.nsh"
!include "LogicLib.nsh"
!include shortcut-properties.nsh

BrandingText "Mulgyeol Labs"

AllowSkipFiles off

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "mkbot_install.ico"
!define MUI_UNICON "mkbot_install.ico"

; Welcome page
!define MUI_WELCOMEFINISHPAGE_BITMAP "..\resources\package\welcome.bmp"
!insertmacro MUI_PAGE_WELCOME
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_CHECKED
!define MUI_FINISHPAGE_RUN_FUNCTION "RunMDF"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"
;!insertmacro MUI_LANGUAGE "Korean"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "MKBotSetup.exe"
InstallDir "$LOCALAPPDATA\Programs\Mulgyeol MK Bot"
InstallDirRegKey HKCU "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Var installOption
Var ReadyToUpdate
Var MAINDIR
; 0 = unpack
; 1 = general
; 2 = update

Function RmDirsButOne
 Exch $R0 ; exclude dir
 Exch
 Exch $R1 ; route dir
 Push $R2
 Push $R3
 
  ClearErrors
  FindFirst $R3 $R2 "$R1\*.*"
  IfErrors Exit
 
  Top:
    StrCmp $R2 "." Next
    StrCmp $R2 ".." Next
    StrCmp $R2 $R0 Next
    IfFileExists "$R1\$R2\*.*" 0 Next
    RmDir /r "$R1\$R2"
 
  Next:
    ClearErrors
    FindNext $R3 $R2
    IfErrors Exit
    Goto Top
 
  Exit:
  FindClose $R3
 
 Pop $R3
 Pop $R2
 Pop $R1
 Pop $R0
FunctionEnd

Function RmFilesButOne
 Exch $R0 ; exclude file
 Exch
 Exch $R1 ; route dir
 Push $R2
 Push $R3
 
  FindFirst $R3 $R2 "$R1\*.*"
  IfErrors Exit
 
  Top:
   StrCmp $R2 "." Next
   StrCmp $R2 ".." Next
   StrCmp $R2 $R0 Next
   IfFileExists "$R1\$R2\*.*" Next
    Delete "$R1\$R2"
 
   #Goto Exit ;uncomment this to stop it being recursive (delete only one file)
 
   Next:
    ClearErrors
    FindNext $R3 $R2
    IfErrors Exit
   Goto Top
 
  Exit:
  FindClose $R3
 
 Pop $R3
 Pop $R2
 Pop $R1
 Pop $R0
FunctionEnd

Function .onInit
  ;!insertmacro MUI_LANGDLL_DISPLAY
  StrCpy $MAINDIR "$LOCALAPPDATA\Programs\Mulgyeol MK Bot"
  StrCpy $installOption 1
  StrCpy $INSTDIR "$LOCALAPPDATA\Programs\Mulgyeol MK Bot"
  ${GetParameters} $1
  ClearErrors
  ${GetOptions} $1 '/unpack' $R0
  IfErrors +3 0
  StrCpy $INSTDIR "$LOCALAPPDATA\Programs\Mulgyeol MK Bot\_"
  StrCpy $installOption 0
  ClearErrors
  ${GetOptions} $1 '/update' $R0
  IfErrors +3 0
  StrCpy $INSTDIR "$LOCALAPPDATA\Programs\Mulgyeol MK Bot"
  StrCpy $installOption 2
FunctionEnd

Function RunMDF
  SetOutPath "$INSTDIR"
  Exec "$INSTDIR\MKBot.exe"
FunctionEnd

Section "Apps" SEC01
  ${If} $installOption > 0
    nsExec::Exec 'taskkill /f /im "MKBot.exe"'
  ${EndIf}

  IfSilent +1 +4
  SetSilent Normal
  HideWindow
  SetAutoClose true

  ${If} $installOption < 2
    ${If} $installOption == 0
      IfFileExists "$INSTDIR\*.*" +1 +2
      RMDir /r "$INSTDIR"
    ${EndIf}
    SetOutPath "$INSTDIR"
    File "Update.exe"
    ${If} $installOption == 0
      Delete "$INSTDIR\..\Update.exe"
      Rename "$INSTDIR\Update.exe" "$INSTDIR\..\Update.exe"
    ${EndIf}
    File /nonfatal /a "..\build\*"
    File "MKBot.VisualElementsManifest.xml"
    SetOutPath "$INSTDIR\app"
    File /nonfatal /a /r "..\build\app\*"
    SetOutPath "$INSTDIR\info"
    File /nonfatal /a /r "info\*"
    SetOutPath "$INSTDIR\resources\app"
    File /nonfatal /a /r "..\resources\app\*"
    SetOutPath "$LOCALAPPDATA\Mulgyeol\Mulgyeol MK Bot\data"
    SetOverwrite off
    File /nonfatal /a /r "data\*"
    SetOverwrite on
    SetOutPath "$PROFILE\.mkbot\extensions"
    File /nonfatal /a /r "..\extensions\*"
  ${ElseIf} $installOption == 2
    ReadRegStr $ReadyToUpdate HKCU "${PRODUCT_DIR_REGKEY}" "ReadyToUpdate"
    ${If} $ReadyToUpdate == "1"
      Push "$INSTDIR"
      Push "Update.exe"
      Call RmFilesButOne
      Push "$INSTDIR" 
      Push "_" 		;dir to exclude
      Call RmDirsButOne
      CopyFiles /SILENT "$INSTDIR\_\*" "$INSTDIR"
      RMDir /r "$INSTDIR\_"
    ${Else}
      Abort
    ${EndIf}
  ${EndIf}

  ${If} $installOption < 2
    SetOutPath "$MAINDIR"
    CreateDirectory "$SMPROGRAMS\MK Bot"
    CreateShortCut "$SMPROGRAMS\MK Bot\MK Bot.lnk" "$MAINDIR\MKBot.exe"
    !insertmacro ShortcutSetToastProperties "$SMPROGRAMS\MK Bot\MK Bot.lnk" "{3f7eb835-ef29-45f5-acb5-a078d127dc94}" "com.mgylabs.mkbot"
    CreateShortCut "$DESKTOP\MK Bot.lnk" "$MAINDIR\MKBot.exe"
  ${EndIf}
  ;ExecWait 'schtasks.exe /Delete /TN "MKBotUpdate" /F'
  ;Exec 'schtasks.exe /Create /TN "MKBotUpdate" /XML "$INSTDIR\Update\MKBotUpdate.xml"'
  ;ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe install'
  ;ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe start'
SectionEnd

Section -AdditionalIcons
  ${If} $installOption < 2
    WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
    CreateShortCut "$SMPROGRAMS\MK Bot\Website.lnk" "$MAINDIR\${PRODUCT_NAME}.url"
    CreateShortCut "$SMPROGRAMS\MK Bot\Uninstall.lnk" "$MAINDIR\uninst.exe"
  ${EndIf}
SectionEnd

Section -Post
  ${If} $installOption < 2
    WriteUninstaller "$INSTDIR\uninst.exe"
    WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "" "$MAINDIR\MKBot.exe"
    WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "Path" "$MAINDIR"
    ${If} $installOption == 1
      WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "ReadyToUpdate" "0"
    ${Else}
      WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "ReadyToUpdate" "1"
    ${EndIf}
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$MAINDIR\uninst.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$MAINDIR\MKBot.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION_NUMBER}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Mulgyeol MK Bot" "$MAINDIR\MKBot.exe"
  ${ElseIf} $installOption == 2
    WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "ReadyToUpdate" "0"
  ${EndIf}
SectionEnd

Function .onInstSuccess
  ${If} $installOption == 2
    ${GetParameters} $1
    ClearErrors
    ${GetOptions} $1 '/autorun' $R0
    IfErrors +4 0
    SetOutPath "$INSTDIR"
    Exec "$INSTDIR\MKBot.exe"
  ${EndIf}
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "${PRODUCT_NAME} was successfully removed from your computer." /SD IDOK
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove ${PRODUCT_NAME} and all of its components?" /SD IDYES IDYES +2
  Abort
FunctionEnd

Section Uninstall
  ;Exec 'schtasks.exe /Delete /TN "MKBotUpdate" /F'
  ;ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe stop'
  ;ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe remove'
  nsExec::Exec 'taskkill /f /im "MKBot.exe"'
  Delete "$SMPROGRAMS\MK Bot\Uninstall.lnk"
  Delete "$SMPROGRAMS\MK Bot\Website.lnk"
  Delete "$DESKTOP\MK Bot.lnk"
  Delete "$SMPROGRAMS\MK Bot\MK Bot.lnk"

  RMDir "$SMPROGRAMS\MK Bot"
  RMDir /r /REBOOTOK $MAINDIR

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKCU "${PRODUCT_DIR_REGKEY}"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Mulgyeol MK Bot"
  SetAutoClose true
SectionEnd