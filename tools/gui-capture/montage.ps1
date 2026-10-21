param([string[]]$files)
Add-Type -AssemblyName System.Drawing; $tw=900; $th=540; $n=$files.Count; $cols=2; [int]$rows=[math]::Ceiling($n/2)
$bm=New-Object Drawing.Bitmap([int](1800),[int](540*$rows)); $g=[Drawing.Graphics]::FromImage($bm)
for($k=0;$k -lt $n;$k++){ $i=[Drawing.Image]::FromFile($files[$k]); $g.DrawImage($i,($k%$cols)*$tw,[math]::Floor($k/$cols)*$th,$tw,$th); $g.DrawString((Split-Path $files[$k] -Leaf),(New-Object Drawing.Font('Arial',18)),[Drawing.Brushes]::Yellow,($k%$cols)*$tw+5,[math]::Floor($k/$cols)*$th+5); $i.Dispose() }
$m=New-Object IO.MemoryStream; $bm.Save($m,[Drawing.Imaging.ImageFormat]::Jpeg); [IO.File]::WriteAllText("$env:USERPROFILE\agent-tools\preview.b64",[Convert]::ToBase64String($m.ToArray()))

