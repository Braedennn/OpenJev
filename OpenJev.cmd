@echo off
setlocal
title OpenJev
set "ROOT=%~dp0"
set "PATH=%ROOT%tools\node;%PATH%"

set "DESK=%ROOT%harness\apps\desktop\.desktop-build\targets\win-x64\unsigned-artifacts"
if exist "%DESK%\win-unpacked\OpenJev.exe" (
  start "" "%DESK%\win-unpacked\OpenJev.exe"
) else (
  for /f "delims=" %%i in ('dir /b /s "%DESK%\openjev-*-win-x64.exe" 2^>nul') do start "" "%%i"
)
