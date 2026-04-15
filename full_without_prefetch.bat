@echo off
REM Full NX filelist without prefetch - usage: full_without_prefetch.bat [num_processes]
set NPROC=%1
if "%NPROC%"=="" set NPROC=4
echo Starting with %NPROC% process(es) at %TIME%
if exist c:\HEC\out rd /s /q c:\HEC\out
md c:\HEC\out
echo %TIME%
C:\git\exchange_core\build_irt\bin\RelWithDebInfo\HoopsExchangeChecker.exe -filelist C:\git\exchange_core\exchange\admin\QA\Filelist\filelist_NX.txt -config c:\HEC\config_loadonly.xml -settings c:\git\exchange_core\exchange\admin\QA\Configuration\Import\NX\settings.xml -libdir c:\git\exchange_core\build_irt\bin\RelWithDebInfo -process %NPROC% -removeduplicate=off -out c:\HEC\out
echo %TIME%
