$outputFile = "process_count.txt"

"Time,Count_processes" | Out-File -FilePath $outputFile -Encoding utf8

$startTime = Get-Date

while ($true) {
    $currentTime = Get-Date -Format "HH:mm:ss"

    $processCount = (Get-Process).Count

    "$currentTime,$processCount" | Out-File -FilePath $outputFile -Append -Encoding utf8

    $elapsedTime = (Get-Date) - $startTime
    if ($elapsedTime.TotalSeconds -ge 60) {
        break
    }

    Start-Sleep -Seconds 1
}
