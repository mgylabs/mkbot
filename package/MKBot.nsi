!define PRODUCT_NAME "MK Bot"
; !define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Mulgyeol Labs"
!define PRODUCT_WEB_SITE "https://www.mgylabs.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\MKBot.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKCU"

Unicode true
RequestExecutionLevel user
; MUI 1.67 compatible ------
!include "MUI.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "mkbot_install.ico"
!define MUI_UNICON "mkbot_install.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
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
!insertmacro MUI_LANGUAGE "Korean"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "MKBotSetup.exe"
InstallDir "$LOCALAPPDATA\Programs\MK Bot"
InstallDirRegKey HKCU "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Function .onInit
  StrCpy $INSTDIR "$LOCALAPPDATA\Programs\MK Bot"
FunctionEnd

Function RunMDF
  SetOutPath "$INSTDIR"
  Exec "$INSTDIR\MKBot.exe"
FunctionEnd

Section "Apps" SEC01
  ; nsExec::Exec 'taskkill /f /im "Mulgyeol Software Update.exe"'
  SetOutPath "$INSTDIR"
  File "msu.exe"
  IfSilent +1 +2
  Exec "$INSTDIR\msu.exe /start MKBotSetup.exe"
  File /nonfatal /a /r "..\build\MKBot.exe"
  SetOutPath "$INSTDIR\app"
  File /nonfatal /a /r "..\build\app\*"
  CreateDirectory "$SMPROGRAMS\MK Bot"
  CreateShortCut "$SMPROGRAMS\MK Bot\MK Bot.lnk" "$INSTDIR\MKBot.exe"
  CreateShortCut "$DESKTOP\MK Bot.lnk" "$INSTDIR\MKBot.exe"
  SetOutPath "$INSTDIR\info"
  File /nonfatal /a /r "info\*"
  SetOutPath "$INSTDIR\data"
  SetOverwrite off
  File /nonfatal /a /r "data\*"
  SetOverwrite on
  ;ExecWait 'schtasks.exe /Delete /TN "MKBotUpdate" /F'
  ;Exec 'schtasks.exe /Create /TN "MKBotUpdate" /XML "$INSTDIR\Update\MKBotUpdate.xml"'
  ;ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe install'
  ;ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe start'
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\MK Bot\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\MK Bot\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\MKBot.exe"
  WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "Path" "$INSTDIR"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\MKBot.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "MK Bot" "$INSTDIR\MKBot.exe"
SectionEnd

Function .onInstSuccess
    IfSilent +1 +3
		SetOutPath "$INSTDIR"
		Exec "$INSTDIR\MKBot.exe"
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "${PRODUCT_NAME}는(은) 완전히 제거되었습니다." /SD IDOK
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "${PRODUCT_NAME}을(를) 제거하시겠습니까?" /SD IDYES IDYES +2
  Abort
  nsExec::Exec 'taskkill /f /im "MKBot.exe"'
FunctionEnd

Section Uninstall
  ;Exec 'schtasks.exe /Delete /TN "MKBotUpdate" /F'
  ;ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe stop'
  ;ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe remove'
  Delete "$SMPROGRAMS\MK Bot\Uninstall.lnk"
  Delete "$SMPROGRAMS\MK Bot\Website.lnk"
  Delete "$DESKTOP\MK Bot.lnk"
  Delete "$SMPROGRAMS\MK Bot\MK Bot.lnk"

  RMDir "$SMPROGRAMS\MK Bot"
  RMDir /r /REBOOTOK $INSTDIR

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKCU "${PRODUCT_DIR_REGKEY}"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "MK Bot"
  SetAutoClose true
SectionEnd