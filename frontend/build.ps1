<#
.SYNOPSIS
    Compila o front-end (Vite + Vue + Tailwind + DaisyUI) usando um diretório local em C:
    para evitar erros de EBADF/lentidão do node_modules em unidades virtuais como o Google Drive (G:\).
#>

$ErrorActionPreference = "Stop"

$FrontendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkDir = Join-Path $env:LOCALAPPDATA "AgendaMedica\frontend-build"
$LockHashFile = Join-Path $WorkDir ".lockhash"

New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null

# Sincroniza apenas os arquivos fonte (sem node_modules nem dist)
foreach ($arquivo in @("index.html", "package.json", "package-lock.json", "vite.config.js")) {
    $origem = Join-Path $FrontendDir $arquivo
    if (Test-Path $origem) {
        Copy-Item -Path $origem -Destination (Join-Path $WorkDir $arquivo) -Force
    }
}

$srcDestino = Join-Path $WorkDir "src"
if (Test-Path $srcDestino) {
    Remove-Item -Path $srcDestino -Recurse -Force
}
Copy-Item -Path (Join-Path $FrontendDir "src") -Destination $srcDestino -Recurse -Force

# Instala dependências apenas na primeira vez ou quando package-lock.json mudar
$lockPath = Join-Path $WorkDir "package-lock.json"
$hashAtual = if (Test-Path $lockPath) { (Get-FileHash $lockPath -Algorithm SHA256).Hash } else { "" }
$hashAnterior = if (Test-Path $LockHashFile) { Get-Content $LockHashFile -Raw } else { "" }

Push-Location $WorkDir
try {
    if (-not (Test-Path (Join-Path $WorkDir "node_modules")) -or ($hashAtual -ne $hashAnterior.Trim())) {
        Write-Host "Instalando dependências do front-end em $WorkDir..." -ForegroundColor Cyan
        if (Test-Path $lockPath) {
            npm ci
        } else {
            npm install
        }
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Set-Content -Path $LockHashFile -Value $hashAtual -NoNewline
    }

    Write-Host "Gerando build de produção (Vite)..." -ForegroundColor Cyan
    npm run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}

# Copia o dist atualizado de volta para o projeto
$distDestino = Join-Path $FrontendDir "dist"
if (Test-Path $distDestino) {
    Remove-Item -Path $distDestino -Recurse -Force
}
Copy-Item -Path (Join-Path $WorkDir "dist") -Destination $distDestino -Recurse -Force

Write-Host "Build atualizado com sucesso em: $distDestino" -ForegroundColor Green
