$MaxCount = 9
$Count = 0

while ($Count -lt $MaxCount) {
    Start-Process powershell -ArgumentList "& { Start-Sleep -Seconds 0.3; Start-Process powershell -ArgumentList '& { Start-Sleep -Seconds 0.3; Start-Process powershell -ArgumentList '' }' }"
    $Count++
    Start-Sleep -Seconds 0.3
}
