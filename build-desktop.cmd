@echo off
setlocal
title Build OpenJev desktop
set "ROOT=%~dp0"
set "PATH=%ROOT%tools\node;%PATH%"
cd /d "%ROOT%harness"
call pnpm install
call pnpm run build
call pnpm package:desktop:win:x64:unsigned
echo.
echo Build finished. Artifacts: harness\apps\desktop\.desktop-build\targets\win-x64\unsigned-artifacts
pause
