@echo off
REM Full NX filelist with prefetch - usage: full_with_prefetch.bat [num_processes] [boost_count]
REM   full_with_prefetch.bat 4       - normal order (small first)
REM   full_with_prefetch.bat 4 50    - boost 50 heaviest models to front of prefetch queue
set NPROC=%1
if "%NPROC%"=="" set NPROC=4
set EXTRA_ARGS=
if not "%2"=="" set EXTRA_ARGS=-prefetch-boost %2
echo Starting with %NPROC% process(es) %EXTRA_ARGS% at %TIME%
if exist c:\HEC\out rd /s /q c:\HEC\out
md c:\HEC\out
echo %TIME%
C:\git\exchange_core\build_irt\bin\RelWithDebInfo\HoopsExchangeChecker.exe -filelist C:\git\exchange_core\exchange\admin\QA\Filelist\filelist_NX.txt -config c:\HEC\config_loadonly.xml -settings c:\git\exchange_core\exchange\admin\QA\Configuration\Import\NX\settings.xml -libdir c:\git\exchange_core\build_irt\bin\RelWithDebInfo -prefetch -process %NPROC% -cachedir c:\HEC\cache\Import_NX -removeduplicate=off -out c:\HEC\out %EXTRA_ARGS%
echo %TIME%
