Add-Type @"
using System;using System.Runtime.InteropServices;
public class K{[DllImport("user32.dll")]public static extern void keybd_event(byte v,byte s,int f,int e);}
"@
[W]::ShowWindow([IntPtr]$w.Current.NativeWindowHandle,6)|Out-Null
$h=(Get-Process orca-slicer|?{$_.MainWindowHandle -ne 0}|select -First 1).MainWindowHandle
[K]::keybd_event(0x12,0,0,0); [K]::keybd_event(0x12,0,2,0)
[W]::ShowWindow($h,9)|Out-Null; [W]::ShowWindow($h,3)|Out-Null; $r=[W]::SetForegroundWindow($h); "fg $r" | Add-Content $log; Start-Sleep 2
