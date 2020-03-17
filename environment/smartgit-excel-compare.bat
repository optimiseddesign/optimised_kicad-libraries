@ECHO OFF
rem In Smartgit - in Preferences, add a Diff Tool for e.g. *.xls pattern and set to this script
rem smartgit diff passes two arguments: old-file, new-file.
set TEMP_FILE=%TEMP%\smartgit-excel-diff.txt
ECHO %1 > %TEMP_FILE%
ECHO %2 >> %TEMP_FILE%
"C:\Program Files (x86)\Microsoft Office\root\Office16\DCF\spreadsheetcompare.exe" %TEMP_FILE%