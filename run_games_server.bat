@echo off
title ECO 414 Games server
rem Starts the lecturer server. Students on the same Wi-Fi or lab network join at the address shown.
where python 1>NUL 2>NUL
if %errorlevel%==0 (python "%~dp0server.py" %*) else (py "%~dp0server.py" %*)
pause
