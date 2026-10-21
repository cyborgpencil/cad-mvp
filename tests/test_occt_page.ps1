# Headless Edge check of the web OCCT gate. Not a CTest target.
# Requires libcascade staged under web/dist and cadcam.wasm built.
$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path "$PSScriptRoot\..").Path
$Py = (Get-Command py -ErrorAction SilentlyContinue).Source
if ($Py) { $PyArgs = @('-3') } else {
  $Py = (Get-Command python -ErrorAction SilentlyContinue).Source
  $PyArgs = @()
}
if (-not $Py) { throw 'Python not found' }
$Edge = @(
  'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
  'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Edge) { throw 'msedge.exe not found' }

$Port = 8766
$Prof = Join-Path $Repo 'builds\edge-wasm-occt'
New-Item -ItemType Directory -Force -Path $Prof | Out-Null

$server = Start-Process $Py -ArgumentList ($PyArgs + @('-m','http.server',"$Port",'--directory',(Join-Path $Repo 'web'))) -WorkingDirectory $Repo -PassThru -WindowStyle Hidden
Start-Sleep 1
$edgeProc = $null
$ws = $null
try {
  $edgeProc = Start-Process $Edge -ArgumentList @(
    '--headless=new','--disable-gpu','--remote-debugging-port=9334',
    "--user-data-dir=$Prof",'--no-first-run','--no-default-browser-check',
    'about:blank'
  ) -PassThru
  Start-Sleep 3
  $pages = Invoke-RestMethod 'http://127.0.0.1:9334/json'
  $tab = $pages | Where-Object { $_.type -eq 'page' } | Select-Object -First 1
  $ws = New-Object Net.WebSockets.ClientWebSocket
  $ws.ConnectAsync([Uri]$tab.webSocketDebuggerUrl, [Threading.CancellationToken]::None).Wait()
  $script:msgId = 0
  function Cdp($method, $params = @{}) {
    $script:msgId++
    $payload = @{ id = $script:msgId; method = $method; params = $params } | ConvertTo-Json -Depth 12 -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($payload)
    $ws.SendAsync([ArraySegment[byte]]$bytes, 'Text', $true, [Threading.CancellationToken]::None).Wait()
    while ($true) {
      $ms = New-Object IO.MemoryStream
      do {
        $buf = New-Object byte[] 1048576
        $r = $ws.ReceiveAsync([ArraySegment[byte]]$buf, [Threading.CancellationToken]::None).Result
        $ms.Write($buf, 0, $r.Count)
      } until ($r.EndOfMessage)
      $json = [Text.Encoding]::UTF8.GetString($ms.ToArray()) | ConvertFrom-Json
      if ($json.id -eq $script:msgId) { return $json }
    }
  }
  function Wait-Gate($url, $timeoutSec) {
    Cdp 'Page.navigate' @{ url = $url } | Out-Null
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    $probe = 'window.__cadcamExportState ? JSON.stringify(window.__cadcamExportState) : ""'
    do {
      Start-Sleep -Milliseconds 500
      $r = Cdp 'Runtime.evaluate' @{ expression = $probe; returnByValue = $true }
      $text = [string]$r.result.result.value
      if ($text -and $text.StartsWith('{')) {
        $st = $text | ConvertFrom-Json
        if ($st.occtReady) { return $st }
      }
    } while ((Get-Date) -lt $deadline)
    throw "Timed out waiting for OCCT gate at $url"
  }
  $closed = Wait-Gate "http://127.0.0.1:$Port/?fixture=closed_box&tab=export" 90
  $open = Wait-Gate "http://127.0.0.1:$Port/?fixture=open_box&tab=export" 90
  $script:fail = 0
  function Expect($name, $ok) {
    if ($ok) { return }
    Write-Host "FAIL $name"
    $script:fail++
  }
  Expect 'closed occt green' ($closed.occtGate -eq $true)
  Expect 'closed export on' ($closed.exportAllowed -eq $true -and $closed.exportDisabled -eq $false)
  Expect 'closed banner gone' ($closed.bannerHidden -eq $true)
  Expect 'closed badge PASS' ($closed.gateOcct -eq 'PASS')
  Expect 'open occt red' ($open.occtGate -eq $false)
  Expect 'open export locked' ($open.exportAllowed -eq $false -and $open.exportDisabled -eq $true)
  Expect 'open banner stays' ($open.bannerHidden -eq $false)
  Expect 'open badge FAIL' ($open.gateOcct -eq 'FAIL')
  Write-Host ('closed=' + ($closed | ConvertTo-Json -Compress))
  Write-Host ('open=' + ($open | ConvertTo-Json -Compress))
  if ($fail -ne 0) { throw "$fail page checks failed" }
  Write-Host 'ok'
} finally {
  if ($ws) { $ws.Dispose() }
  if ($edgeProc) { Stop-Process -Id $edgeProc.Id -Force -ErrorAction SilentlyContinue }
  Get-Process msedge -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $Edge } | Stop-Process -Force -ErrorAction SilentlyContinue
  if ($server) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
}
