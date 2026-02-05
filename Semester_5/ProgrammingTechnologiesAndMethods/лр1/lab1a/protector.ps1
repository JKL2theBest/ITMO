# Кодировка UTF-8 с BOM

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("setup", "on", "off", "status", "watch")]
    [string]$Mode
)

# Запрос прав и настройка
$currentUser = New-Object -TypeName Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Definition)`" -Mode $Mode"
    Start-Process -FilePath "powershell.exe" -Verb "RunAs" -ArgumentList $arguments
    exit
}
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -Path $scriptPath
$TemplateFile = "template.tbl"
$everyoneSid = New-Object -TypeName System.Security.Principal.SecurityIdentifier("S-1-1-0") # ВСЕ

Function Set-FileDenyFullControl {
    param($FilePath)
    
    if (-not (Test-Path -Path $FilePath)) { return }

    $acl = Get-Acl -Path $FilePath
    $permissions = [System.Security.AccessControl.FileSystemRights]::FullControl
    $rule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule($everyoneSid, $permissions, "Deny")

    $acl.Access |
        Where-Object { $_.IdentityReference -eq $everyoneSid -and $_.AccessControlType -eq "Deny" } |
        ForEach-Object { $acl.RemoveAccessRule($_) }

    $acl.AddAccessRule($rule)
    Set-Acl -Path $FilePath -AclObject $acl
}

# Выполнение режима
switch ($Mode) {
    "setup" {
        Write-Host "--- Первоначальная настройка ---"
        if (Test-Path $TemplateFile) {
            $confirm = Read-Host "'template.tbl' уже существует. Перезаписать? (y/n)"
            if ($confirm -ne 'y') { Write-Host "Отмена."; exit }
        }
        while ($true) {
            $securePassword = Read-Host -Prompt "Введите новый пароль" -AsSecureString
            if ($securePassword.Length -eq 0) {
                Write-Host "Пароль не может быть пустым." -ForegroundColor Red
                continue
            }
            $securePasswordConfirm = Read-Host -Prompt "Подтвердите пароль" -AsSecureString

            $bstr1 = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
            $plainText1 = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr1)
            $bstr2 = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePasswordConfirm)
            $plainText2 = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr2)
            $passwordsMatch = ($plainText1 -eq $plainText2)
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr1)
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr2)
            
            if ($passwordsMatch) { break }
            else { Write-Host "Пароли не совпадают. Пожалуйста, попробуйте снова." -ForegroundColor Red }
        }

        $rng = New-Object -TypeName System.Security.Cryptography.RNGCryptoServiceProvider
        $saltBytes = [byte[]]::new(16); $rng.GetBytes($saltBytes)
        $salt = [System.Convert]::ToBase64String($saltBytes)
        $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        $plainTextPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

        $sha256 = New-Object -TypeName System.Security.Cryptography.SHA256Managed
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($salt + $plainTextPassword)
        $passwordHash = [System.BitConverter]::ToString($sha256.ComputeHash($bytes)).Replace('-', '').ToLower()

        $fileContent = "$salt`:$passwordHash`nsecret_document.txt`nreport_*.docx`n*.log"
        Set-Content -Path $TemplateFile -Value $fileContent -Encoding UTF8
        Write-Host "'template.tbl' успешно создан/обновлен." -ForegroundColor Green
    }
    "status" {
        if (-not (Test-Path $TemplateFile)) { Write-Host "Не настроено."; exit }
        try { Get-Content -Path $TemplateFile -ErrorAction Stop -TotalCount 1 | Out-Null; Write-Host "Статус защиты: OFF" -ForegroundColor Red }
        catch { Write-Host "Статус защиты: ON" -ForegroundColor Green }
    }
    "on" {
        Write-Host "Включение защиты..." -ForegroundColor Yellow
        if (-not (Test-Path $TemplateFile)) { Write-Host "Ошибка: 'template.tbl' не найден."; exit }
        try { Get-Content -Path $TemplateFile -ErrorAction Stop -TotalCount 1 | Out-Null }
        catch { Write-Host "Защита уже включена." -ForegroundColor Green; exit }

        $patterns = Get-Content -Path $TemplateFile -Encoding UTF8 | Select-Object -Skip 1
        $targetFiles = @(Get-ChildItem -Path . -File -Recurse | Where-Object { $file = $_; $patterns | Where-Object { $file.Name -like $_ } })
        $targetFiles += Get-Item -Path $TemplateFile
        $uniqueFiles = $targetFiles | Get-Unique
        
        if ($uniqueFiles) {
            Write-Host "Применяется защита к следующим файлам:"
            $uniqueFiles.FullName | ForEach-Object { Write-Host " - $_" }
        } else {
            Write-Host "Не найдено файлов для защиты." -ForegroundColor Yellow
        }
        
        foreach ($file in $uniqueFiles) {
            Set-FileDenyFullControl -FilePath $file.FullName
        }
        Write-Host "`nЗащита включена." -ForegroundColor Green
    }
    "off" {
        Write-Host "Отключение защиты..." -ForegroundColor Yellow
        if (-not (Test-Path $TemplateFile)) { Write-Host "Ошибка: 'template.tbl' не найден."; exit }
        try { Get-Content -Path $TemplateFile -ErrorAction Stop -TotalCount 1 | Out-Null; Write-Host "Защита уже выключена." -ForegroundColor Red; exit }
        catch { }

        $ruleToRemove = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule($everyoneSid, "FullControl", "Deny")
        $acl = Get-Acl -Path $TemplateFile; $acl.RemoveAccessRuleSpecific($ruleToRemove); Set-Acl -Path $TemplateFile -AclObject $acl

        $salt, $storedHash = (Get-Content -Path $TemplateFile -Encoding UTF8)[0].Split(':')
        
        $plainTextPassword = ""
        if ($Host.Name -eq "ConsoleHost" -and ($Host.UI.RawUI.KeyAvailable -or -not [Console]::IsInputRedirected)) {
            $securePassword = Read-Host -Prompt "Введите пароль" -AsSecureString
            $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword);
            $plainTextPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr);
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        } else { $plainTextPassword = [Console]::In.ReadLine() }

        $sha256 = New-Object -TypeName System.Security.Cryptography.SHA256Managed
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($salt + $plainTextPassword)
        $passwordHash = [System.BitConverter]::ToString($sha256.ComputeHash($bytes)).Replace('-', '').ToLower()
        
        if ($passwordHash -ne $storedHash) {
            Write-Host "Неверный пароль! Возвращаем защиту обратно." -ForegroundColor Red
            $acl = Get-Acl -Path $TemplateFile; $acl.AddAccessRule($ruleToRemove); Set-Acl -Path $TemplateFile -AclObject $acl
            exit
        }

        Write-Host "Пароль верный. Отключаем защиту..." -ForegroundColor Green
        $patterns = Get-Content -Path $TemplateFile -Encoding UTF8 | Select-Object -Skip 1
        $targetFiles = @(Get-ChildItem -Path . -File -Recurse | Where-Object { $file = $_; $patterns | Where-Object { $file.Name -like $_ } })
        $targetFiles += Get-Item -Path $TemplateFile
        $uniqueFiles = $targetFiles | Get-Unique

        if ($uniqueFiles) {
            Write-Host "Снимается защита со следующих файлов:"
            $uniqueFiles.FullName | ForEach-Object { Write-Host " - $_" }
        }

        foreach ($file in $uniqueFiles) {
            $acl = Get-Acl -Path $file.FullName; $acl.RemoveAccessRuleSpecific($ruleToRemove); Set-Acl -Path $file.FullName -AclObject $acl
        }
        Write-Host "`nЗащита отключена." -ForegroundColor Red
    }
    "watch" {
        Write-Host "--- РЕЖИМ СЛЕЖЕНИЯ АКТИВИРОВАН ---"
        if (-not (Test-Path $TemplateFile)) { Write-Host "Ошибка: 'template.tbl' не найден."; exit }
        
        $patterns = (Get-Content $TemplateFile -Encoding UTF8) | Select-Object -Skip 1
        $watcher = New-Object System.IO.FileSystemWatcher
        $watcher.Path = $scriptPath; $watcher.IncludeSubdirectories = $true; $watcher.NotifyFilter = [System.IO.NotifyFilters]'FileName, DirectoryName'
        
        $action = {
            $filePath = $event.SourceEventArgs.FullPath; $fileName = $event.SourceEventArgs.Name; $changeType = $event.SourceEventArgs.ChangeType
            if ($patterns | Where-Object { $fileName -like $_ }) {
                Write-Host "Событие '$changeType': $fileName"
                Start-Sleep -Milliseconds 100
                Set-FileDenyFullControl -FilePath $filePath
                Write-Host " -> Файл защищен." -ForegroundColor Green
            }
        }
        Register-ObjectEvent $watcher "Created" -Action $action | Out-Null
        Register-ObjectEvent $watcher "Renamed" -Action $action | Out-Null
        $watcher.EnableRaisingEvents = $true
        while ($true) { Start-Sleep -Seconds 1 }
    }
}