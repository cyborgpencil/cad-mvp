. "$PSScriptRoot\orcafront.ps1"; Click 1542 1015; Start-Sleep 2
[W]::SetCursorPos(1600,700); Start-Sleep -m 300; [K]::keybd_event(0x30,0,0,0); [K]::keybd_event(0x30,0,2,0); Start-Sleep 2
Shot $AE::RootElement '08-orca-3mf'
