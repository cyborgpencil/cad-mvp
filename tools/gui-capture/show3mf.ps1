Get-ChildItem $PSScriptRoot\..\..\builds\screenshots\export | Format-Table Name,Length,LastWriteTime -Auto
Add-Type -AssemblyName System.IO.Compression.FileSystem; $z=[IO.Compression.ZipFile]::OpenRead('$PSScriptRoot\..\..\builds\screenshots\export\box.3mf'); $m=$z.Entries|?{$_.FullName -like '*.model'}; $t=(New-Object IO.StreamReader($m.Open())).ReadToEnd(); $z.Dispose()
'3MF model header:'; ($t -split '>')[0..1] -join ">`n"
