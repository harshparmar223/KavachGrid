@echo off
:: Batch script to configure Mosquitto for LAN (0.0.0.0) and restart the service
:: Automatically requests Administrator privileges if not already elevated

title Fix Mosquitto LAN Access for ESP32 Nodes

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator privileges to configure Mosquitto service...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ================================================================
echo   Configuring Mosquitto MQTT Broker for LAN (ESP32) Access
echo ================================================================
echo.

set "CONF_FILE=C:\Program Files\mosquitto\mosquitto.conf"

if not exist "%CONF_FILE%" (
    echo [ERROR] Mosquitto config not found at: %CONF_FILE%
    pause
    exit /b 1
)

:: Check if listener 1883 0.0.0.0 is already present
findstr /C:"listener 1883 0.0.0.0" "%CONF_FILE%" >nul
if %errorLevel% equ 0 (
    echo [INFO] Mosquitto configuration already contains 'listener 1883 0.0.0.0'.
) else (
    echo [INFO] Adding 'listener 1883 0.0.0.0' and 'allow_anonymous true' to mosquitto.conf...
    echo.>> "%CONF_FILE%"
    echo # Enabled for KavachGrid ESP32 nodes on local network>> "%CONF_FILE%"
    echo listener 1883 0.0.0.0>> "%CONF_FILE%"
    echo allow_anonymous true>> "%CONF_FILE%"
)

echo [INFO] Restarting Mosquitto Windows Service...
powershell -Command "Restart-Service mosquitto"

echo.
echo ================================================================
echo   [SUCCESS] Mosquitto is now listening on 0.0.0.0:1883!
echo   ESP32 nodes can now connect to 192.168.0.106:1883.
echo ================================================================
echo.
pause
