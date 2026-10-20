@echo off
rem Copies the offline games file to the Public Desktop so every user on this lab computer sees it.
rem Run from the USB stick (or shared folder) that holds "ECO414 Games (offline).html".
set "SRC=%~dp0ECO414 Games (offline).html"
if not exist "%SRC%" (
  echo Cannot find "%SRC%". Keep this file next to the games file.
  pause
  exit /b 1
)
copy /Y "%SRC%" "%PUBLIC%\Desktop\ECO414 Games.html" >nul 2>&1
if errorlevel 1 (
  echo No permission for the Public Desktop; copying to this user's Desktop instead.
  copy /Y "%SRC%" "%USERPROFILE%\Desktop\ECO414 Games.html" >nul
)
echo Done. Open "ECO414 Games" on the desktop with Chrome or Edge.
pause
