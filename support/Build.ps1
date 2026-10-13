$ErrorActionPreference = 'Stop'
$kitRoot = Split-Path -Parent $PSScriptRoot
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$sources = @('SteamMain.cs', 'SteamProbe.cs', 'SteamTunnel.cs', 'SteamWindow.cs') | ForEach-Object { Join-Path $PSScriptRoot $_ }
& $compiler /nologo /platform:x86 /target:winexe "/out:$kitRoot\OmertaSteamCoop.exe" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll $sources
if ($LASTEXITCODE -ne 0) { throw 'Launcher compilation failed' }
