# protector.ps1
# ВАЖНО: Этот файл должен быть сохранен в кодировке "UTF-8 с BOM"

param (
    [Parameter(Mandatory = $true)]
    [ValidateSet("setup", "on", "off", "status")]
    [string]$Mode
)

# --- Блок 1: Запрос прав и настройка ---
$currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Definition)`" -Mode $Mode"
    Start-Process powershell -Verb RunAs -ArgumentList $arguments
    exit
}

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath
$TemplateFile = "template.tbl"
$sid = [System.Security.Principal.SecurityIdentifier]::new("S-1-1-0") # Everyone

# --- Блок 2: Выполнение режима ---

if ($Mode -eq "setup") {
    Write-Host "--- Первоначальная настройка ---" -ForegroundColor Yellow
    if (Test-Path $TemplateFile) {
        $confirm = Read-Host "Файл 'template.tbl' уже существует. Перезаписать? (y/n)"
        if ($confirm -ne 'y') { Write-Host "Настройка отменена."; exit }
    }
    $SecurePassword = Read-Host -Prompt "Введите новый пароль" -AsSecureString
    if ($SecurePassword.Length -eq 0) { Write-Host "Пароль не может быть пустым." -ForegroundColor Red; exit }
    
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::new()
    $saltBytes = [byte[]]::new(16); $rng.GetBytes($saltBytes)
    $salt = [System.Convert]::ToBase64String($saltBytes)

    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
    $PlainTextPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    
    $sha256 = [System.Security.Cryptography.SHA256Managed]::new()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($salt + $PlainTextPassword)
    $PasswordHash = [System.BitConverter]::ToString($sha256.ComputeHash($bytes)).Replace('-', '').ToLower()
    
    $fileContent = "$salt`:$PasswordHash`nsecret_document.txt`nreport_*.docx`n*.log"
    Set-Content -Path $TemplateFile -Value $fileContent -Encoding UTF8
    Write-Host "Файл 'template.tbl' успешно создан/обновлен." -ForegroundColor Green

} elseif ($Mode -eq "status") {
    if (-not (Test-Path $TemplateFile)) { Write-Host "Не настроено."; exit }
    try {
        Get-Content $TemplateFile -ErrorAction Stop -TotalCount 1 | Out-Null
        Write-Host "Статус защиты: ВЫКЛЮЧЕНА" -ForegroundColor Green
    } catch {
        Write-Host "Статус защиты: ВКЛЮЧЕНА" -ForegroundColor Red
    }

} elseif ($Mode -eq "on") {
    Write-Host "Включение защиты..." -ForegroundColor Yellow
    if (-not (Test-Path $TemplateFile)) { Write-Host "Ошибка: 'template.tbl' не найден."; exit }
    
    try { Get-Content $TemplateFile -ErrorAction Stop -TotalCount 1 | Out-Null }
    catch { Write-Host "Защита уже включена." -ForegroundColor Yellow; exit }
    
    $patterns = (Get-Content $TemplateFile -Encoding UTF8) | Select-Object -Skip 1
    $targetFiles = Get-ChildItem -Path . -File -Recurse | Where-Object { $p = $_.Name; $patterns | Where-Object { $p -like $_ } }
    $targetFiles += Get-Item $TemplateFile

    foreach ($file in ($targetFiles | Get-Unique)) {
        $acl = Get-Acl $file.FullName
        $permissions = [System.Security.AccessControl.FileSystemRights]::FullControl
        $rule = [System.Security.AccessControl.FileSystemAccessRule]::new($sid, $permissions, "Deny")
        $acl.AddAccessRule($rule)
        Set-Acl -Path $file.FullName -AclObject $acl
    }
    Write-Host "Защита включена (полный запрет)." -ForegroundColor Green

} elseif ($Mode -eq "off") {
    Write-Host "Отключение защиты..." -ForegroundColor Yellow
    if (-not (Test-Path $TemplateFile)) { Write-Host "Ошибка: 'template.tbl' не найден."; exit }

    try {
        Get-Content $TemplateFile -ErrorAction Stop -TotalCount 1 | Out-Null
        Write-Host "Защита уже выключена." -ForegroundColor Yellow
        exit
    } catch { }

    # ШАГ 1: Создаем "ключ" - точную копию правила FullControl, которое нужно удалить.
    $ruleToRemove = [System.Security.AccessControl.FileSystemAccessRule]::new(
        $sid, [System.Security.AccessControl.FileSystemRights]::FullControl, "Deny"
    )
    $acl = Get-Acl $TemplateFile
    # Используем единственно надежный метод для удаления такого мощного правила
    $acl.RemoveAccessRuleSpecific($ruleToRemove)
    Set-Acl -Path $TemplateFile -AclObject $acl
    
    # ШАГ 2: Теперь, когда файл доступен, читаем хэш и проверяем пароль
    $salt, $StoredHash = ((Get-Content $TemplateFile -Encoding UTF8)[0]).Split(':')
    $SecurePassword = Read-Host -Prompt "Введите пароль" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
    $PlainTextPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    
    $sha256 = [System.Security.Cryptography.SHA256Managed]::new()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($salt + $PlainTextPassword)
    $PasswordHash = [System.BitConverter]::ToString($sha256.ComputeHash($bytes)).Replace('-', '').ToLower()
    
    if ($PasswordHash -ne $StoredHash) {
        Write-Host "Неверный пароль! Возвращаем защиту обратно." -ForegroundColor Red
        $acl = Get-Acl $TemplateFile
        $acl.AddAccessRule($ruleToRemove) # Используем тот же "ключ", чтобы запереть обратно
        Set-Acl -Path $TemplateFile -AclObject $acl
        exit
    }

    # ШАГ 3: Пароль верный. Снимаем защиту со всех остальных файлов.
    Write-Host "Пароль верный. Отключаем защиту..." -ForegroundColor Green
    $patterns = (Get-Content $TemplateFile -Encoding UTF8) | Select-Object -Skip 1
    $targetFiles = Get-ChildItem -Path . -File -Recurse | Where-Object { $p = $_.Name; $patterns | Where-Object { $p -like $_ } }
    
    foreach ($file in ($targetFiles | Get-Unique)) {
        $acl = Get-Acl $file.FullName
        $acl.RemoveAccessRuleSpecific($ruleToRemove) # Удаляем то же самое правило FullControl
        Set-Acl -Path $file.FullName -AclObject $acl
    }
    Write-Host "Защита отключена (полный доступ восстановлен)." -ForegroundColor Green
}