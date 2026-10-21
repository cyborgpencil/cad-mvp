Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes,System.Windows.Forms,System.Drawing
Add-Type @"
using System;using System.Runtime.InteropServices;
public class W{[DllImport("user32.dll")]public static extern bool SetForegroundWindow(IntPtr h);[DllImport("user32.dll")]public static extern bool ShowWindow(IntPtr h,int c);[DllImport("user32.dll")]public static extern bool SetCursorPos(int x,int y);[DllImport("user32.dll")]public static extern void mouse_event(int f,int x,int y,int d,int e);[DllImport("kernel32.dll")]public static extern uint SetThreadExecutionState(uint e);}
"@
[W]::SetThreadExecutionState([uint32]2147483651) | Out-Null
$Repo=(Resolve-Path "$PSScriptRoot\..\..").Path; $S="$Repo\builds\screenshots"; New-Item -ItemType Directory "$S\scripts" -Force|Out-Null; $log="$S\scripts\run.log"
$QtBin=if($env:QT_BIN){$env:QT_BIN}else{'C:\Qt\6.8.3\msvc2022_64\bin'}; $env:PATH="$QtBin;"+$env:PATH
$AE=[Windows.Automation.AutomationElement]
function Win{ $p=Get-Process solid_view -EA 0|select -First 1; if(!$p){$p=Start-Process "$Repo\builds\solid-check\solid_view.exe" -WorkingDirectory $Repo -PassThru; Start-Sleep 8}
 $c=New-Object Windows.Automation.PropertyCondition($AE::ProcessIdProperty,$p.Id); $w=$AE::RootElement.FindFirst('Children',$c); [W]::ShowWindow([IntPtr]$w.Current.NativeWindowHandle,3)|Out-Null; [W]::SetForegroundWindow([IntPtr]$w.Current.NativeWindowHandle)|Out-Null; Start-Sleep 1; $w}
function El($w,$id){ foreach($e in $w.FindAll('Descendants',[Windows.Automation.Condition]::TrueCondition)){ $a=$e.Current.AutomationId; if($a -eq $id -or $a.EndsWith('.'+$id)){ return $e } } }
function Btn($w,$name){ $c=New-Object Windows.Automation.AndCondition((New-Object Windows.Automation.PropertyCondition($AE::NameProperty,$name)),(New-Object Windows.Automation.PropertyCondition($AE::ControlTypeProperty,[Windows.Automation.ControlType]::Button))); $b=$w.FindFirst('Descendants',$c); $b.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke(); Start-Sleep 2 }
function SetV($w,$n,$v){ $e=El $w ('spin_'+$n); $e.GetCurrentPattern([Windows.Automation.RangeValuePattern]::Pattern).SetValue($v) }
function Res($w,$t){ "[$t] result: $((El $w 'watertight-result').Current.Name) | $((El $w 'measure-readout').Current.Name)" | Add-Content $log }
function Shot($w,$name){ Start-Sleep 1; $r=$w.Current.BoundingRectangle; $b=New-Object Drawing.Bitmap([int]$r.Width,[int]$r.Height); $g=[Drawing.Graphics]::FromImage($b); $g.CopyFromScreen([int]$r.X,[int]$r.Y,0,0,$b.Size); $b.Save("$S\$name.png"); $g.Dispose(); $b.Dispose() }
function Click($x,$y){ [W]::SetCursorPos($x,$y); Start-Sleep -m 200; [W]::mouse_event(2,0,0,0,0); Start-Sleep -m 80; [W]::mouse_event(4,0,0,0,0); Start-Sleep 1 }
try{ $w=Win; "win $($w.Current.BoundingRectangle)" | Add-Content $log; . "$PSScriptRoot\cmd.ps1" }catch{ "ERR $_ @ $($_.InvocationInfo.ScriptLineNumber): $($_.InvocationInfo.Line)" | Add-Content $log }
