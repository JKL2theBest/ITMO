# Кодировка UTF-8 с BOM

# Запрос прав и настройка
$currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$($MyInvocation.MyCommand.Definition)`""
    Start-Process powershell -Verb RunAs -ArgumentList $arguments
    exit
}
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath
$ProtectorScript = Join-Path $scriptPath "protector.ps1"
$TemplateFile = "template.tbl"

if (-not (Test-Path $TemplateFile)) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        "Файл 'template.tbl' не найден.`nСначала запустите 'start.bat setup'.",
        "Программа не настроена", "OK", "Error"
    )
    exit
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName Microsoft.VisualBasic

# Создание GUI
$form = New-Object System.Windows.Forms.Form
$form.Text = "Файловый Протектор (1а)"
$form.Size = [System.Drawing.Size]::new(450, 200)
$form.MinimumSize = [System.Drawing.Size]::new(450, 200)
$form.StartPosition = "CenterScreen"

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = "Защита файлов:"
$statusLabel.Location = [System.Drawing.Point]::new(20, 20)
$statusLabel.Font = [System.Drawing.Font]::new("Arial", 10)
$statusLabel.AutoSize = $true

$statusValue = New-Object System.Windows.Forms.Label
$statusValue.Location = [System.Drawing.Point]::new(130, 18)
$statusValue.Font = [System.Drawing.Font]::new([string]"Arial", [float]10, [System.Drawing.FontStyle]::Bold)
$statusValue.AutoSize = $true

$onButton = New-Object System.Windows.Forms.Button
$onButton.Text = "ВКЛЮЧИТЬ ВСЕ"
$onButton.Size = [System.Drawing.Size]::new(180, 40)
$onButton.Location = [System.Drawing.Point]::new(20, 60)
$onButton.BackColor = [System.Drawing.Color]

$offButton = New-Object System.Windows.Forms.Button
$offButton.Text = "ВЫКЛЮЧИТЬ ВСЕ"
$offButton.Size = [System.Drawing.Size]::new(180, 40)
$offButton.Location = [System.Drawing.Point]::new(220, 60)
$offButton.BackColor = [System.Drawing.Color]

$logButton = New-Object System.Windows.Forms.Button
$logButton.Text = "Показать логи ▼"
$logButton.Size = [System.Drawing.Size]::new(120, 25)
$logButton.Location = [System.Drawing.Point]::new(20, 120)

$logBox = New-Object System.Windows.Forms.TextBox
$logBox.Multiline = $true
$logBox.ScrollBars = "Vertical"
$logBox.ReadOnly = $true
$logBox.Location = [System.Drawing.Point]::new(20, 160)
$logBox.Size = [System.Drawing.Size]::new(400, 200)
$logBox.Visible = $false
$logBox.Font = [System.Drawing.Font]::new("Consolas", 9)

$logTimer = New-Object System.Windows.Forms.Timer
$logTimer.Interval = 1000

$form.Controls.AddRange(@(
    $statusLabel, $statusValue,
    $onButton, $offButton, $logButton, $logBox
))

# Логика
Set-Variable -Name WatchJob -Value $null -Scope Script

Function Write-Log ($message) {
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logBox.AppendText("[$timestamp] $message`r`n")
}

Function Invoke-Protector($Mode, $InputString = $null) {
    # Функция для вызова protector.ps1 и получения его вывода
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = "powershell.exe"
    $pinfo.RedirectStandardOutput = $true
    $pinfo.UseShellExecute = $false
    $pinfo.CreateNoWindow = $true
    $pinfo.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$ProtectorScript`" -Mode $Mode"
    
    if ($InputString) { $pinfo.RedirectStandardInput = $true }

    $p = [System.Diagnostics.Process]::Start($pinfo)
    if ($InputString) {
        $p.StandardInput.WriteLine($InputString)
        $p.StandardInput.Close()
    }
    $output = $p.StandardOutput.ReadToEnd()
    $p.WaitForExit()
    return $output
}

Function Update-All-Statuses {
    $output = Invoke-Protector -Mode "status"
    $status = $output.Split(':')[-1].Trim()
    $statusValue.Text = $status
    if ($status -eq "ON") { $statusValue.ForeColor = 'Green' } 
    else { $statusValue.ForeColor = 'Red' }
    
    if ($script:WatchJob) { $watchStatusValue.Text = "ВКЛЮЧЕНО"; $watchStatusValue.ForeColor = 'Green' }
    else { $watchStatusValue.Text = "ВЫКЛЮЧЕНО"; $watchStatusValue.ForeColor = 'Red' }
    
    if ($status -eq "ON" -or $script:WatchJob) { $onButton.Enabled = $false; $offButton.Enabled = $true }
    else { $onButton.Enabled = $true; $offButton.Enabled = $false }
}

$onButton.Add_Click({
    Write-Log "Команда: ВКЛЮЧИТЬ ВСЕ"
    Write-Log "Запуск слежения в фоновом режиме..."
    $script:WatchJob = Start-Job -ScriptBlock { 
        param($script)
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script -Mode watch 
    } -ArgumentList $ProtectorScript
    $logTimer.Start()
    Write-Log "Слежение запущено (Job ID: $($script:WatchJob.Id))."
    
    Write-Log "Защита существующих файлов..."
    $output = Invoke-Protector -Mode "on"
    $output.Split("`n") | ForEach-Object { if ($_.Trim()) { Write-Log $_.Trim() } }
    Update-All-Statuses
})

$offButton.Add_Click({
    Write-Log "Команда: ВЫКЛЮЧИТЬ ВСЕ"
    $password = [Microsoft.VisualBasic.Interaction]::InputBox("Введите пароль для отключения:", "Пароль")
    if ($password) {
        Write-Log "Отключение защиты файлов..."
        $output = Invoke-Protector -Mode "off" -InputString $password
        $output.Split("`n") | ForEach-Object { if ($_.Trim()) { Write-Log $_.Trim() } }

        if ($output -like "*Пароль верный*") {
            if ($script:WatchJob) {
                Write-Log "Остановка слежения..."
                $script:WatchJob | Stop-Job -Force
                $script:WatchJob | Remove-Job -Force
                $script:WatchJob = $null
                $logTimer.Stop()
                Write-Log "Слежение остановлено."
            }
        }
    } else { Write-Log "Отключение отменено." }
    Update-All-Statuses
})

$logTimer.Add_Tick({
    if ($script:WatchJob) {
        $output = $script:WatchJob | Receive-Job
        if ($output) {
            $output.Split("`n") | ForEach-Object { if ($_.Trim()) { Write-Log "Слежение: $($_.Trim())" } }
        }
    }
})

$logButton.Add_Click({
    if ($logBox.Visible) {
        $form.Size = [System.Drawing.Size]::new(450, 200)
        $logBox.Visible = $false
        $logButton.Text = "Показать логи ▼"
    } else {
        $form.Size = [System.Drawing.Size]::new(450, 430)
        $logBox.Visible = $true
        $logButton.Text = "Скрыть логи ▲"
    }
})

$form.Add_FormClosing({
    if ($script:WatchJob) {
        $script:WatchJob | Stop-Job -Force
        $script:WatchJob | Remove-Job -Force
    }
})

Update-All-Statuses
[void]$form.ShowDialog()