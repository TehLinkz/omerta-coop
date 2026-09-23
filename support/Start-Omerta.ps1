# Experimental launcher bypass. No signed executable is modified.
[CmdletBinding()]
param(
    [string]$GameDirectory = 'D:\SteamLibrary\steamapps\common\Omerta',
    [switch]$Windowed,
    [ValidateRange(800,7680)][int]$Width = 1920,
    [ValidateRange(600,4320)][int]$Height = 1080
)
$ErrorActionPreference = 'Stop'
$gameRoot = (Resolve-Path -LiteralPath $GameDirectory).Path.TrimEnd('\')
$gameExe = Join-Path $gameRoot 'OmertaSteam.exe'
$helperExe = Join-Path $gameRoot 'AppData.exe'
if (!(Test-Path -LiteralPath $gameExe) -or !(Test-Path -LiteralPath $helperExe)) {
    throw 'Omerta executable or launcher helper is missing.'
}
$existing = @(Get-CimInstance Win32_Process -Filter "Name='OmertaSteam.exe'" |
    Where-Object { $_.ExecutablePath -eq $gameExe })
if ($existing.Count) { throw 'Close Omerta before using this launcher.' }
if (-not ('OmertaLauncherExit' -as [type])) {
    Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class OmertaLauncherExit {
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool TerminateProcess(IntPtr process, uint code);
    [DllImport("kernel32.dll")]
    static extern bool CloseHandle(IntPtr handle);
    public static void Offline(uint pid) {
        IntPtr handle = OpenProcess(1, false, pid);
        if (handle == IntPtr.Zero) throw new System.ComponentModel.Win32Exception();
        try {
            if (!TerminateProcess(handle, 128)) throw new System.ComponentModel.Win32Exception();
        } finally { CloseHandle(handle); }
    }
}
'@
}
$started = Get-Date
if ($Windowed) {
    $steamRoot = (Get-ItemProperty 'HKCU:\Software\Valve\Steam').SteamPath
    $steamExe = Join-Path $steamRoot 'steam.exe'
    if (!(Test-Path -LiteralPath $steamExe)) { throw 'Steam executable not found.' }
    Start-Process -FilePath $steamExe -ArgumentList @('-applaunch', '208520', '-windowed', '-width', "$Width", '-height', "$Height") -WindowStyle Hidden
} else {
    Start-Process 'steam://rungameid/208520'
}
$deadline = $started.AddSeconds(90)
while ((Get-Date) -lt $deadline) {
    $games = @(Get-CimInstance Win32_Process -Filter "Name='OmertaSteam.exe'" |
        Where-Object { $_.ExecutablePath -eq $gameExe -and $_.CreationDate -ge $started.AddSeconds(-2) })
    foreach ($game in $games) {
        $helpers = @(Get-CimInstance Win32_Process -Filter "Name='AppData.exe'" |
            Where-Object { $_.ParentProcessId -eq $game.ProcessId -and $_.ExecutablePath -eq $helperExe -and $_.CommandLine -like '*OMSTM*' })
        foreach ($helper in $helpers) {
            # 128 is the helper's native KeyOkOffline return code.
            # Scope termination to this new Omerta process's verified child.
            $children = @(Get-CimInstance Win32_Process -Filter "Name='KalypsoLauncher.exe'" |
                Where-Object { $_.ParentProcessId -eq $helper.ProcessId -and $_.CommandLine -like '*OMSTM*' })
            [OmertaLauncherExit]::Offline([uint32]$helper.ProcessId)
            foreach ($child in $children) { Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue }
            Write-Output 'Omerta helper returned offline status. Verify the game reaches its main menu.'
            exit 0
        }
    }
    Start-Sleep -Milliseconds 100
}
throw 'No matching Omerta launcher helper appeared within 90 seconds. No unrelated process was stopped.'
