;!define PRODUCT_NAME "Mulgyeol MK Bot"
;!define PRODUCT_EXE "MKBot.exe"
; !define PRODUCT_VERSION "1.0.0"
; !define EXT_DIR ".mkbot"
!searchreplace PRODUCT_VERSION_NUMBER "${PRODUCT_VERSION}" " Canary" ""
!searchreplace PRODUCT_SHORT_NAME "${PRODUCT_NAME}" "Mulgyeol " ""
!define PRODUCT_PUBLISHER "Mulgyeol Labs"
!define PRODUCT_WEB_SITE "https://github.com/mgylabs/mulgyeol-mkbot"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\${PRODUCT_EXE}"
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
!define MUI_ICON "..\resources\package\mkbot.ico"
!define MUI_UNICON "..\resources\package\mkbot.ico"

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
OutFile "..\MKBotSetup.exe"
InstallDir "$LOCALAPPDATA\Programs\${PRODUCT_NAME}"
InstallDirRegKey HKCU "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Var installOption
Var MAINDIR
; 0 = unpack
; 1 = general

Function .onInit
  ;!insertmacro MUI_LANGDLL_DISPLAY
  StrCpy $MAINDIR "$LOCALAPPDATA\Programs\${PRODUCT_NAME}"
  StrCpy $installOption 1
  StrCpy $INSTDIR "$LOCALAPPDATA\Programs\${PRODUCT_NAME}"
  ${GetParameters} $1
  ClearErrors
  ${GetOptions} $1 '/unpack' $R0
  IfErrors +3 0
  StrCpy $INSTDIR "$LOCALAPPDATA\Programs\${PRODUCT_NAME}\_"
  StrCpy $installOption 0
FunctionEnd

Function WriteToFile
  Exch $0 ;file to write to
  Exch
  Exch $1 ;text to write

    FileOpen $0 $0 a #open file
    FileSeek $0 0 END #go to end
    FileWrite $0 $1 #write to file
    FileClose $0

  Pop $1
  Pop $0
FunctionEnd

Function WriteFlag
  Push `flag` ;text to write to file
  Push `$MAINDIR\Update.flag` ;file to write to
  Call WriteToFile
FunctionEnd

Function RunMDF
  SetOutPath "$INSTDIR"
  Exec "$INSTDIR\${PRODUCT_EXE}"
FunctionEnd

Section "Apps" SEC01
  Delete `$MAINDIR\Update.flag`

  ${If} $installOption > 0
    nsExec::Exec 'taskkill /f /im "${PRODUCT_EXE}"'
  ${EndIf}

  IfSilent +1 +4
  SetSilent Normal
  HideWindow
  SetAutoClose true

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
  SetOutPath "$PROFILE\${EXT_DIR}\extensions"
  File /nonfatal /a /r "..\extensions\*"

  SetOutPath "$MAINDIR"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_SHORT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_SHORT_NAME}\${PRODUCT_SHORT_NAME}.lnk" "$MAINDIR\${PRODUCT_EXE}"
  !insertmacro ShortcutSetToastProperties "$SMPROGRAMS\${PRODUCT_SHORT_NAME}\${PRODUCT_SHORT_NAME}.lnk" "{3f7eb835-ef29-45f5-acb5-a078d127dc94}" "com.mgylabs.mkbot"
  CreateShortCut "$DESKTOP\${PRODUCT_SHORT_NAME}.lnk" "$MAINDIR\${PRODUCT_EXE}"
  ;ExecWait 'schtasks.exe /Delete /TN "MKBotUpdate" /F'
  ;Exec 'schtasks.exe /Create /TN "MKBotUpdate" /XML "$INSTDIR\Update\MKBotUpdate.xml"'
  ;ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe install'
  ;ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe start'
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_SHORT_NAME}\Website.lnk" "$MAINDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_SHORT_NAME}\Uninstall.lnk" "$MAINDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "" "$MAINDIR\${PRODUCT_EXE}"
  WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "Path" "$MAINDIR"
  ${If} $installOption == 0
    Call WriteFlag
  ${EndIf}
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$MAINDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$MAINDIR\${PRODUCT_EXE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION_NUMBER}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${PRODUCT_NAME}" "$MAINDIR\${PRODUCT_EXE}"
SectionEnd

Function .onInstSuccess
  ${If} $installOption != 0
    ${GetParameters} $1
    ClearErrors
    ${GetOptions} $1 '/autorun' $R0
    IfErrors +4 0
    SetOutPath "$INSTDIR"
    Exec "$INSTDIR\${PRODUCT_EXE}"
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
  nsExec::Exec 'taskkill /f /im "${PRODUCT_EXE}"'
  Delete "$SMPROGRAMS\${PRODUCT_SHORT_NAME}\Uninstall.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_SHORT_NAME}\Website.lnk"
  Delete "$DESKTOP\${PRODUCT_SHORT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_SHORT_NAME}\${PRODUCT_SHORT_NAME}.lnk"

  RMDir "$SMPROGRAMS\${PRODUCT_SHORT_NAME}"
  RMDir /r /REBOOTOK $INSTDIR

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKCU "${PRODUCT_DIR_REGKEY}"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${PRODUCT_NAME}"
  SetAutoClose true
SectionEnd
