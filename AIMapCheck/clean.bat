@echo off
echo Cleaning project...
rmdir /s /q node_modules
del /f /q package-lock.json
echo Installing dependencies...
npm install
echo Done!
pause
