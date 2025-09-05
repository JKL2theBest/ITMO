# gui.ps1
# ВАЖНО: Этот файл должен быть сохранен в кодировке "UTF-8 с BOM"

# --- Блок 1: Запрос прав и настройка ---
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
$sid = [System.Security.Principal.SecurityIdentifier]::new("S-1-1-0") # Everyone

if (-not (Test-Path $TemplateFile)) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show("Файл 'template.tbl' не найден.`nСначала запустите 'start.bat setup'.", "Программа не настроена", "OK", "Error")
    exit
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName Microsoft.VisualBasic

# --- Блок 2: Ключевые функции (теперь внутри GUI) ---

Function Get-ProtectionStatus {
    try { Get-Content $TemplateFile -ErrorAction Stop -TotalCount 1 | Out-Null; return "ВЫКЛЮЧЕНА" }
    catch { return "ВКЛЮЧЕНА" }
}

Function Get-TargetFiles {
    # Эта функция читает шаблоны ТОЛЬКО когда файл доступен
    $patterns = (Get-Content $TemplateFile -Encoding UTF8) | Select-Object -Skip 1
    $targetFiles = Get-ChildItem -Path . -File -Recurse | Where-Object { $p = $_.Name; $patterns | Where-Object { $p -like $_ } }
    $targetFiles += Get-Item $TemplateFile
    return ($targetFiles | Get-Unique)
}

# --- Блок 3: Создание GUI ---
$form = New-Object System.Windows.Forms.Form; $form.Text = "Файловый Протектор"; $form.Size = [System.Drawing.Size]::new(450, 200); $form.MinimumSize = [System.Drawing.Size]::new(450, 200); $form.StartPosition = "CenterScreen"
$statusLabel = New-Object System.Windows.Forms.Label; $statusLabel.Text = "Защита файлов:"; $statusLabel.Location = [System.Drawing.Point]::new(20, 20); $statusLabel.Font = [System.Drawing.Font]::new("Arial", 10); $statusLabel.AutoSize = $true
$statusValue = New-Object System.Windows.Forms.Label; $statusValue.Location = [System.Drawing.Point]::new(130, 18); $statusValue.Font = [System.Drawing.Font]::new([string]"Arial", [float]10, [System.Drawing.FontStyle]::Bold); $statusValue.AutoSize = $true
$onButton = New-Object System.Windows.Forms.Button; $onButton.Text = "ВКЛЮЧИТЬ ВСЕ"; $onButton.Size = [System.Drawing.Size]::new(180, 40); $onButton.Location = [System.Drawing.Point]::new(20, 60); $onButton.BackColor = [System.Drawing.Color]
$offButton = New-Object System.Windows.Forms.Button; $offButton.Text = "ВЫКЛЮЧИТЬ ВСЕ"; $offButton.Size = [System.Drawing.Size]::new(180, 40); $offButton.Location = [System.Drawing.Point]::new(220, 60); $offButton.BackColor = [System.Drawing.Color]
$logButton = New-Object System.Windows.Forms.Button; $logButton.Text = "Показать логи ▼"; $logButton.Size = [System.Drawing.Size]::new(120, 25); $logButton.Location = [System.Drawing.Point]::new(20, 120)
$logBox = New-Object System.Windows.Forms.TextBox; $logBox.Multiline = $true; $logBox.ScrollBars = "Vertical"; $logBox.ReadOnly = $true; $logBox.Location = [System.Drawing.Point]::new(20, 160); $logBox.Size = [System.Drawing.Size]::new(400, 200); $logBox.Visible = $false; $logBox.Font = [System.Drawing.Font]::new("Consolas", 9)
$logTimer = New-Object System.Windows.Forms.Timer; $logTimer.Interval = 1000
$form.Controls.AddRange(@($statusLabel, $statusValue, $watchStatusLabel, $watchStatusValue, $onButton, $offButton, $logButton, $logBox))

# --- Блок 4: Логика GUI ---
Set-Variable -Name WatchJob -Value $null -Scope Script

Function Write-Log ($message) { $timestamp = Get-Date -Format "HH:mm:ss"; $logBox.AppendText("[$timestamp] $message`r`n") }

Function Update-All-Statuses {
    $status = Get-ProtectionStatus
    $statusValue.Text = $status
    if ($status -eq "ВКЛЮЧЕНА") { $statusValue.ForeColor = 'Red' } else { $statusValue.ForeColor = 'Green' }
    if ($script:WatchJob) { $watchStatusValue.Text = "ВКЛЮЧЕНО"; $watchStatusValue.ForeColor = 'Red' } else { $watchStatusValue.Text = "ВЫКЛЮЧЕНО"; $watchStatusValue.ForeColor = 'Green' }
    if ($status -eq "ВКЛЮЧЕНА" -or $script:WatchJob) { $onButton.Enabled = $false; $offButton.Enabled = $true } else { $onButton.Enabled = $true; $offButton.Enabled = $false }
}

$onButton.Add_Click({
    Write-Log "Команда: ВКЛЮЧИТЬ ВСЕ"
    # Шаг 1: Запускаем слежение
    Write-Log "Запуск слежения в фоновом режиме..."
    $script:WatchJob = Start-Job -ScriptBlock { param($script) ; powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script -Mode watch } -ArgumentList $ProtectorScript
    $logTimer.Start(); Write-Log "Слежение запущено (Job ID: $($script:WatchJob.Id))."
    # Шаг 2: Включаем защиту для существующих файлов
    Write-Log "Защита существующих файлов..."; $files = Get-TargetFiles
    foreach ($file in $files) {
        $acl = Get-Acl $file.FullName; $rule = [System.Security.AccessControl.FileSystemAccessRule]::new($sid, "FullControl", "Deny"); $acl.AddAccessRule($rule); Set-Acl -Path $file.FullName -AclObject $acl
    }
    Write-Log "Защита для существующих файлов включена."; Update-All-Statuses
})

$offButton.Add_Click({
    Write-Log "Команда: ВЫКЛЮЧИТЬ ВСЕ"; $password = [Microsoft.VisualBasic.Interaction]::InputBox("Введите пароль для отключения:", "Пароль")
    if (-not $password) { Write-Log "Отключение отменено."; return }

    # Шаг 1: Снимаем защиту с template.tbl, чтобы прочитать пароль
    $ruleToRemove = [System.Security.AccessControl.FileSystemAccessRule]::new($sid, "FullControl", "Deny")
    $acl = Get-Acl $TemplateFile; $acl.RemoveAccessRuleSpecific($ruleToRemove); Set-Acl -Path $TemplateFile -AclObject $acl
    
    # Шаг 2: Проверяем пароль
    $salt, $StoredHash = ((Get-Content $TemplateFile -Encoding UTF8)[0]).Split(':')
    $sha256 = [System.Security.Cryptography.SHA256Managed]::new(); $bytes = [System.Text.Encoding]::UTF8.GetBytes($salt + $password); $PasswordHash = [System.BitConverter]::ToString($sha256.ComputeHash($bytes)).Replace('-', '').ToLower()
    
    if ($PasswordHash -ne $StoredHash) {
        Write-Log "Неверный пароль! Возвращаем защиту обратно."; $acl = Get-Acl $TemplateFile; $acl.AddAccessRule($ruleToRemove); Set-Acl -Path $TemplateFile -AclObject $acl
    } else {
        Write-Log "Пароль верный. Отключаем всю защиту..."
        # Шаг 3: Снимаем защиту со всех остальных файлов
        $files = Get-TargetFiles
        foreach ($file in $files) {
            $acl = Get-Acl $file.FullName; $acl.RemoveAccessRuleSpecific($ruleToRemove); Set-Acl -Path $file.FullName -AclObject $acl
        }
        # Шаг 4: Останавливаем слежение
        if ($script:WatchJob) {
            Write-Log "Остановка слежения..."; $script:WatchJob | Stop-Job -Force
            $script:WatchJob | Remove-Job -Force; $script:WatchJob = $null
            $logTimer.Stop(); Write-Log "Слежение остановлено."
        }
        Write-Log "Вся защита отключена."
    }
    Update-All-Statuses
})

$logTimer.Add_Tick({ if ($script:WatchJob) { $output = $script:WatchJob | Receive-Job; if ($output) { $output.Split("`n") | ForEach-Object { if ($_.Trim()) { Write-Log "Слежение: $($_.Trim())" } } } } })
$logButton.Add_Click({ if ($logBox.Visible) { $form.Size = [System.Drawing.Size]::new(450, 200); $logBox.Visible = $false; $logButton.Text = "Показать логи ▼" } else { $form.Size = [System.Drawing.Size]::new(450, 430); $logBox.Visible = $true; $logButton.Text = "Скрыть логи ▲" } })
$form.Add_FormClosing({ if ($script:WatchJob) { $script:WatchJob | Stop-Job -Force; $script:WatchJob | Remove-Job -Force } })

Update-All-Statuses
[void]$form.ShowDialog()