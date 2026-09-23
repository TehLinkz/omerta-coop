[CmdletBinding()]
param([switch]$Elevate)
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    if (!$Elevate) { throw 'Administrator rights are required for the host firewall rule.' }
    $process = Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
        -Verb RunAs -WindowStyle Hidden -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"') -Wait -PassThru
    exit $process.ExitCode
}
try {
    $settings = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'host-settings.json') -Raw | ConvertFrom-Json
    $serverExe = Join-Path $PSScriptRoot 'runtime\OmertaCoopServer.exe'
    $address = Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias $settings.interface |
        Where-Object IPAddress -eq $settings.host
    if (!$address -or !(Test-Path -LiteralPath $serverExe)) { throw 'Host interface or runtime no longer matches setup.' }
    $hash = [Security.Cryptography.SHA256]::Create()
    try { $id = ([BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($serverExe.ToLower())))).Replace('-','').Substring(0,12) }
    finally { $hash.Dispose() }
    $ruleName = 'OmertaCoop-Kit-' + $id
    $conflicts = @(Get-NetFirewallApplicationFilter -Program $serverExe -ErrorAction SilentlyContinue | Get-NetFirewallRule |
        Where-Object { $_.Enabled -eq 'True' -and $_.Action -eq 'Block' -and $_.Direction -eq 'Inbound' } |
        Where-Object { ($_ | Get-NetFirewallPortFilter).Protocol -eq 'TCP' })
    if ($conflicts.Count) {
        $conflicts | Export-Clixml (Join-Path $PSScriptRoot ('firewall-block-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.xml'))
        $conflicts | Disable-NetFirewallRule
    }
    $arguments = @{
        Direction='Inbound'; Action='Allow'; Protocol='TCP'; LocalPort=50669
        LocalAddress=$settings.host; RemoteAddress=$settings.subnet; InterfaceAlias=$settings.interface
        Profile='Any'; Program=$serverExe; Enabled='True'
    }
    if (Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue) {
        Set-NetFirewallRule -Name $ruleName @arguments | Out-Null
    } else {
        New-NetFirewallRule -Name $ruleName -DisplayName 'Omerta portable co-op host' @arguments | Out-Null
    }
    ('Firewall ready for ' + $settings.host + ':50669 on ' + $settings.interface) |
        Set-Content (Join-Path $PSScriptRoot 'firewall-result.txt')
} catch {
    $_ | Out-String | Set-Content (Join-Path $PSScriptRoot 'firewall-error.txt')
    exit 1
}
