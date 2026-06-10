; ============================================================
;  Ball Python Breeder Database — NSIS Installer Script
; ============================================================

!include "MUI2.nsh"
!include "LogicLib.nsh"

; ── Sovelluksen perustiedot ──────────────────────────────────
!define APP_NAME        "Ball Python Breeder Database"
!define APP_VERSION     "3.0.0"
!define APP_PUBLISHER   "Myrtillus Reptiles"
!define APP_DESCRIPTION "Ball python breeding management software — From Breeder to Breeders"
!define APP_EXE         "BallPythonDB.exe"
!define APP_ICON        "icon.ico"
!define INSTALL_DIR     "$PROGRAMFILES64\BallPythonDB"
!define UNINSTALL_KEY   "Software\Microsoft\Windows\CurrentVersion\Uninstall\BallPythonDB"

; ── Asennuspaketin asetukset ─────────────────────────────────
Name            "${APP_NAME} ${APP_VERSION}"
OutFile         "Setup_BallPythonDB.exe"
InstallDir      "${INSTALL_DIR}"
InstallDirRegKey HKLM "${UNINSTALL_KEY}" "InstallLocation"
RequestExecutionLevel admin
SetCompressor   lzma
BrandingText    "${APP_PUBLISHER} — ${APP_NAME} ${APP_VERSION}"

; ── Versiotiedot EXE-tiedostoon ─────────────────────────────
; Nämä näkyvät EXE:n Properties → Details -välilehdellä
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName"      "${APP_NAME}"
VIAddVersionKey "ProductVersion"   "${APP_VERSION}"
VIAddVersionKey "CompanyName"      "${APP_PUBLISHER}"
VIAddVersionKey "LegalCopyright"   "© 2024-2026 ${APP_PUBLISHER}"
VIAddVersionKey "FileDescription"  "${APP_DESCRIPTION}"
VIAddVersionKey "FileVersion"      "${APP_VERSION}"
VIAddVersionKey "OriginalFilename" "Setup_BallPythonDB.exe"
VIAddVersionKey "Comments"         "From Breeder to Breeders"

; ── MUI2 ulkoasu ─────────────────────────────────────────────
!define MUI_ABORTWARNING
!define MUI_ICON                "${APP_ICON}"
!define MUI_UNICON              "${APP_ICON}"
!define MUI_WELCOMEPAGE_TITLE   "Welcome to ${APP_NAME} Setup"
!define MUI_WELCOMEPAGE_TEXT    "This will install ${APP_NAME} ${APP_VERSION} on your computer.$\r$\n$\r$\nDeveloped by ${APP_PUBLISHER}$\r$\nFrom Breeder to Breeders$\r$\n$\r$\nClose other applications before continuing."
!define MUI_FINISHPAGE_RUN      "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APP_NAME} now"

; ── Sivut ────────────────────────────────────────────────────
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
Page custom ComponentsPage ComponentsLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ── Komponenttisivu ──────────────────────────────────────────
Var DesktopShortcut
Var StartMenuShortcut

Function ComponentsPage
    nsDialogs::Create 1018
    Pop $0
    ${NSD_CreateLabel} 0 0 100% 20u "Select installation options:"
    ${NSD_CreateCheckbox} 10u 30u 100% 14u "Create desktop shortcut"
    Pop $DesktopShortcut
    ${NSD_SetState} $DesktopShortcut ${BST_CHECKED}
    ${NSD_CreateCheckbox} 10u 50u 100% 14u "Add to Start Menu"
    Pop $StartMenuShortcut
    ${NSD_SetState} $StartMenuShortcut ${BST_CHECKED}
    nsDialogs::Show
FunctionEnd

Function ComponentsLeave
    ${NSD_GetState} $DesktopShortcut  $DesktopShortcut
    ${NSD_GetState} $StartMenuShortcut $StartMenuShortcut
FunctionEnd

; ── Asennus ──────────────────────────────────────────────────
Section "Main Application" SecMain
    SectionIn RO
    SetOutPath "$INSTDIR"
    File "dist\${APP_EXE}"
    File /oname=icon.ico "${APP_ICON}"

    ; Rekisteriavaimet — näkyvät "Apps & Features" -listassa
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayName"          "${APP_NAME}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayVersion"       "${APP_VERSION}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "Publisher"            "${APP_PUBLISHER}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "InstallLocation"      "$INSTDIR"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "UninstallString"      "$INSTDIR\Uninstall.exe"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayIcon"          "$INSTDIR\${APP_EXE}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "Comments"             "${APP_DESCRIPTION}"
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify"             1
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair"             1

    ; Arvioitu asennuskoko kilotavuina (noin 30 Mt)
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "EstimatedSize" 30720

    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Shortcuts" SecShortcuts
    ${If} $StartMenuShortcut == ${BST_CHECKED}
        CreateDirectory "$SMPROGRAMS\${APP_NAME}"
        CreateShortcut  "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" \
                        "$INSTDIR\${APP_EXE}" "" "$INSTDIR\icon.ico"
        CreateShortcut  "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" \
                        "$INSTDIR\Uninstall.exe"
    ${EndIf}
    ${If} $DesktopShortcut == ${BST_CHECKED}
        CreateShortcut  "$DESKTOP\${APP_NAME}.lnk" \
                        "$INSTDIR\${APP_EXE}" "" "$INSTDIR\icon.ico"
    ${EndIf}
SectionEnd

; ── Poisto ───────────────────────────────────────────────────
Section "Uninstall"
    Delete "$INSTDIR\${APP_EXE}"
    Delete "$INSTDIR\icon.ico"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir  "$INSTDIR"

    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"
    RMDir  "$SMPROGRAMS\${APP_NAME}"

    DeleteRegKey HKLM "${UNINSTALL_KEY}"

    MessageBox MB_OK "Uninstall complete.$\r$\nYour data has been kept in:$\r$\n$LOCALAPPDATA\BallPythonDB\ballpython.db$\r$\n$\r$\nDelete this folder manually if you want to remove all data."
SectionEnd
