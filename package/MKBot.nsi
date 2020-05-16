!define PRODUCT_NAME "MK Bot"
; !define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Mulgyeol Labs"
!define PRODUCT_WEB_SITE "https://www.mgylabs.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\MK Bot.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

Unicode true
;RequestExecutionLevel user
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
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Function .onInit
  StrCpy $INSTDIR "$LOCALAPPDATA\Programs\MK Bot"  
FunctionEnd

Function RunMDF
  SetOutPath "$INSTDIR"
  Exec "$INSTDIR\MK Bot"
FunctionEnd

Section "Apps" SEC01
  ExecWait taskkill /f /im "Mulgyeol Software Update.exe"
  SetOutPath "$INSTDIR"
  File /nonfatal /a /r "..\build\*"
  CreateDirectory "$SMPROGRAMS\MK Bot"
  CreateShortCut "$SMPROGRAMS\MK Bot\MK Bot.lnk" "$INSTDIR\MK Bot.exe"
  CreateShortCut "$DESKTOP\MK Bot.lnk" "$INSTDIR\MK Bot.exe"
  SetOutPath "$INSTDIR\data"
  SetOverwrite off
  File /nonfatal /a /r "data\*"
  SetOverwrite on
  ExecWait 'schtasks.exe /Delete /TN "MKBotUpdate" /F'
  Exec 'schtasks.exe /Create /TN "MKBotUpdate" /XML "$INSTDIR\Update\MKBotUpdate.xml"'
  ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe install'
  ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe start'
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\MK Bot\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\MK Bot\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\app\app.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\MK Bot.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "MK Bot" "$INSTDIR\MK Bot.exe"
SectionEnd


Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name)는(은) 완전히 제거되었습니다."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "$(^Name)을(를) 제거하시겠습니까?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  Exec 'schtasks.exe /Delete /TN "MKBotUpdate" /F'
  ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe stop'
  ExecWait '$INSTDIR\Update\MulgyeolUpdateService.exe remove'
  Delete "$SMPROGRAMS\MK Bot\Uninstall.lnk"
  Delete "$SMPROGRAMS\MK Bot\Website.lnk"
  Delete "$DESKTOP\MK Bot.lnk"
  Delete "$SMPROGRAMS\MK Bot\MK Bot.lnk"

  RMDir "$SMPROGRAMS\MK Bot"
  RMDir /r /REBOOTOK $INSTDIR

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "MK Bot"
  SetAutoClose true
SectionEnd