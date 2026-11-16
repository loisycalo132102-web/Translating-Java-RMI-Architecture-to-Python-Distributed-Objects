@echo off
echo Starting Python RMI Distributed Lab Demonstration...
echo.

echo Launching Terminal 1: Pyro5 Server Daemon...
start "Terminal 1: Server Daemon (PYTHON_RMI_LAB/server.py)" cmd /k "python PYTHON_RMI_LAB/server.py"

echo Waiting 2 seconds for server to initialize...
ping 127.0.0.1 -n 3 > nul

echo Launching Terminal 2: Distributed Client...
start "Terminal 2: Client Proxy (PYTHON_RMI_LAB/client.py)" cmd /k "python PYTHON_RMI_LAB/client.py && echo. && echo --- Querying single item: laptop --- && python PYTHON_RMI_LAB/client.py --item laptop"

echo.
echo Both terminals have been launched side-by-side on your desktop!
