REM Without prefetch
echo %TIME%
C:\git\exchange_core\build_irt\bin\RelWithDebInfo\HoopsExchangeChecker.exe -filelist c:\HEC\mini_filelist_NX.txt -config c:\HEC\config_loadonly.xml -settings c:\git\exchange_core\exchange\admin\QA\Configuration\Import\NX\settings.xml -libdir c:\git\exchange_core\build_irt\bin\RelWithDebInfo -process 1 -removeduplicate=off
echo %TIME%
