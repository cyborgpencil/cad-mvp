param($f,$wd=1280)
Add-Type -AssemblyName System.Drawing; $i=[Drawing.Image]::FromFile($f); $b=New-Object Drawing.Bitmap($i,$wd,[int]($wd*$i.Height/$i.Width)); $m=New-Object IO.MemoryStream; $b.Save($m,[Drawing.Imaging.ImageFormat]::Jpeg); $i.Dispose(); [IO.File]::WriteAllText("$env:USERPROFILE\agent-tools\preview.b64",[Convert]::ToBase64String($m.ToArray()))
