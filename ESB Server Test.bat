@echo off
setlocal enabledelayedexpansion

:: Generate a random time between 8 PM and 12 PM
set /a HOUR=%RANDOM% %% 5 + 20
set /a MINUTE=%RANDOM% %% 60
if %HOUR% geq 24 set /a HOUR-=24
if %HOUR% lss 10 set HOUR=0%HOUR%
if %MINUTE% lss 10 set MINUTE=0%MINUTE%

:: Ensure color commands work properly
for /f "tokens=*" %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"

cls

echo %ESC%[93m=====================================
echo         NETWORK STATUS REPORT
echo =====================================%ESC%[0m
echo.

echo %ESC%[97mDate: 28 September 2024
echo Time: %HOUR%:%MINUTE%
echo.

echo %ESC%[92mHOST STATUS: ONLINE
echo - Host IP: 192.168.1.210
echo - Connectivity: Healthy
echo.

echo %ESC%[91mTARGET STATUS: OFFLINE
echo ERROR: Server unresponsive
echo.

echo %ESC%[96mDetails:
echo - Target: https://erp.esb.co.id/
echo - Target IP: 103.28.50.89
echo - Packets sent: 4
echo - Packets received: 0
echo - Packet loss: 100%%
echo.

echo %ESC%[93mRoot cause: https://erp.esb.co.id/ Server unresponsive (possible downtime)
echo Local network connection is stable, but target server is unreachable
echo.

echo %ESC%[92mRecommended actions:
echo 1. Confirm the issue persists from other network locations
echo 2. Check ERP server status with the IT department
echo 3. Verify there are no ongoing maintenance activities
echo 4. Escalate to system administrator if issue persists
echo.

echo %ESC%[97m=====================================
echo Press any key to exit...
pause >nul