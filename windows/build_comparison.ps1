param(
    [ValidateSet('onefile', 'onedir')][string]$Mode = 'onedir',
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Repo = Split-Path $PSScriptRoot -Parent
Set-Location $Repo
$BuildEpoch = & git show -s --format=%ct HEAD
if ($LASTEXITCODE -ne 0 -or $BuildEpoch -notmatch '^\d+$') {
    throw 'Cannot determine reproducible source timestamp'
}
function Invoke-Python {
    $PreviousHashSeed = $env:PYTHONHASHSEED
    $PreviousSourceEpoch = $env:SOURCE_DATE_EPOCH
    try {
        $env:PYTHONHASHSEED = '0'
        $env:SOURCE_DATE_EPOCH = $script:BuildEpoch
        & $script:Python @args
        if ($LASTEXITCODE -ne 0) { throw "Python command failed ($LASTEXITCODE): $args" }
    } finally {
        $env:PYTHONHASHSEED = $PreviousHashSeed
        $env:SOURCE_DATE_EPOCH = $PreviousSourceEpoch
    }
}
# Do not use ambient site-packages or silently change interpreter versions.
Invoke-Python -c "import sys,struct; assert sys.platform == 'win32' and sys.version_info[:3] == (3,13,16) and struct.calcsize('P') == 8, 'Use CPython 3.13.16 Windows x64'"
$Payload = Join-Path $Repo "dist/$Mode"
$Evidence = Join-Path $Repo "build/evidence/$Mode"
if ((Test-Path $Payload) -or (Test-Path $Evidence)) {
    throw 'Output already exists. Preserve previous evidence and move the mode-specific output directories before rebuilding.'
}
$Work = Join-Path $Repo "build/work-$Mode-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $Work, $Evidence | Out-Null
Invoke-Python -m venv "$Work/venv"
$script:Python = Join-Path $Work 'venv/Scripts/python.exe'
Invoke-Python -m pip --isolated install --index-url https://pypi.org/simple --require-hashes --only-binary=:all: --report "$Evidence/install-report.json" -r windows/requirements-build.txt
Invoke-Python -m pip check
Invoke-Python -m pip freeze --all | Set-Content -Encoding utf8 "$Evidence/build-dependencies.txt"
Invoke-Python -m pip inspect | Set-Content -Encoding utf8 "$Evidence/pip-inspect.json"
Invoke-Python -m unittest discover -s tests -p 'test_*.py' -v
Invoke-Python tests/test_structure.py
$Commit = & git rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Cannot determine source commit' }
$Dirty = @(& git status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0) { throw 'Cannot determine source status' }
$PythonVersion = & $script:Python --version
$PipVersion = & $script:Python -m pip --version
@{ mode=$Mode; commit=$Commit; dirty=$Dirty; python=$PythonVersion; pip=$PipVersion;
   image_os=$env:ImageOS; image_version=$env:ImageVersion;
   runner_os=$env:RUNNER_OS; runner_arch=$env:RUNNER_ARCH;
   run_id=$env:GITHUB_RUN_ID; run_attempt=$env:GITHUB_RUN_ATTEMPT;
   python_hash_seed='0'; source_date_epoch=$BuildEpoch;
   flags=@('--clean', "--$Mode", '--windowed', '--noupx')
} | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 "$Evidence/environment.json"
Get-FileHash windows/udc_timer.py, windows/requirements-build.txt, windows/build_comparison.ps1, windows/artifact_inventory.py, windows/compare_builds.py, assets/bell.mp3, .github/workflows/windows-build.yml -Algorithm SHA256 |
    Select-Object @{n='path';e={$_.Path.Substring($Repo.Length + 1)}}, Hash |
    ConvertTo-Json | Set-Content -Encoding utf8 "$Evidence/source-hashes.json"
$BellAsset = Join-Path $Repo 'assets/bell.mp3'
Invoke-Python -m PyInstaller --noconfirm --clean "--$Mode" --windowed --noupx --name PresentationTimer --distpath $Payload --workpath "$Work/pyinstaller" --specpath $Work --add-data "$BellAsset;assets" windows/udc_timer.py
Invoke-Python windows/artifact_inventory.py create $Payload "$Evidence/hashes.json"
Invoke-Python windows/artifact_inventory.py verify $Payload "$Evidence/hashes.json"
Get-ChildItem "$Work/pyinstaller" -Recurse -File -Include 'warn-*.txt', 'xref-*.html' |
    Copy-Item -Destination $Evidence
Write-Output "Built without executing payload: $Payload"
Write-Output "Evidence: $Evidence. Build success does not establish safety."
