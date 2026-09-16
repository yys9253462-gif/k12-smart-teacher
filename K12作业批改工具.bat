@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 936 >nul
title K12 作业批改工具 - 安装与管理

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "LOG_DIR=%ROOT%logs"
set "LOG_FILE=%LOG_DIR%\server.log"
set "HOST=127.0.0.1"
set "PORT=8000"
set "APP_URL=http://%HOST%:%PORT%"
pushd "%ROOT%" >nul

:menu
cls
echo ==================================================
echo             K12 作业批改工具（本地 API 版）
echo ==================================================
echo.
echo   [1] 安装 / 更新运行环境
echo   [2] 启动本地服务
echo   [3] 关闭本地服务
echo   [4] 查看服务状态
echo   [5] 在浏览器打开批改页面
echo.
echo   [0] 退出
echo.
set /p "choice=请输入菜单编号："

if "%choice%"=="1" goto install
if "%choice%"=="2" goto start_server
if "%choice%"=="3" goto stop_server
if "%choice%"=="4" goto status
if "%choice%"=="5" goto open_browser
if "%choice%"=="0" goto end
echo 输入无效，请输入 0 到 5。
pause
goto menu

:find_python
where py >nul 2>nul
if not errorlevel 1 (
    set "BOOTSTRAP_PY=py -3"
    exit /b 0
)
where python >nul 2>nul
if not errorlevel 1 (
    set "BOOTSTRAP_PY=python"
    exit /b 0
)
echo 未找到 Python。请先安装 Python 3.10 或更高版本，并勾选“Add Python to PATH”。
exit /b 1

:install
cls
echo 正在准备本地运行环境……
call :find_python
if errorlevel 1 (
    pause
    goto menu
)
if not exist "%VENV%\Scripts\python.exe" (
    echo 正在创建虚拟环境……
    call %BOOTSTRAP_PY% -m venv "%VENV%"
    if errorlevel 1 (
        echo 创建虚拟环境失败。
        pause
        goto menu
    )
)
echo 正在安装或更新依赖，请稍候……
"%PYTHON%" -m pip install --upgrade pip
"%PYTHON%" -m pip install -r "%ROOT%requirements.txt"
if errorlevel 1 (
    echo.
    echo 安装失败。请检查网络、Python 版本，或查看上方错误信息。
) else (
    echo.
    echo 安装完成。现在可选择“2”启动服务。
)
pause
goto menu

:port_pid
set "SERVER_PID="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
    set "SERVER_PID=%%P"
    goto :eof
)
exit /b 0

:start_server
cls
if not exist "%PYTHON%" (
    echo 尚未安装运行环境，请先选择“1”。
    pause
    goto menu
)
call :port_pid
if defined SERVER_PID (
    echo 服务已经在运行，进程 ID：%SERVER_PID%
    echo 页面地址：%APP_URL%
    pause
    goto menu
)
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo 正在启动服务……
start "K12 作业批改服务" /b cmd /c ""%PYTHON%" -m uvicorn app:app --host %HOST% --port %PORT% > "%LOG_FILE%" 2>&1"
timeout /t 2 /nobreak >nul
call :port_pid
if defined SERVER_PID (
    echo 服务启动成功，进程 ID：%SERVER_PID%
    echo 页面地址：%APP_URL%
    start "" "%APP_URL%"
) else (
    echo 服务未能启动。请查看日志：
    echo %LOG_FILE%
)
pause
goto menu

:stop_server
cls
call :port_pid
if not defined SERVER_PID (
    echo 服务当前未运行。
    pause
    goto menu
)
echo 正在关闭本地服务，进程 ID：%SERVER_PID%
taskkill /PID %SERVER_PID% /F >nul 2>nul
if errorlevel 1 (
    echo 关闭失败。请以管理员身份重新运行此脚本后重试。
) else (
    echo 服务已关闭。
)
pause
goto menu

:status
cls
call :port_pid
if defined SERVER_PID (
    echo 状态：正在运行
    echo 进程 ID：%SERVER_PID%
    echo 页面地址：%APP_URL%
    echo 日志文件：%LOG_FILE%
) else (
    echo 状态：未运行
)
pause
goto menu

:open_browser
cls
call :port_pid
if defined SERVER_PID (
    start "" "%APP_URL%"
    echo 已尝试在默认浏览器中打开：%APP_URL%
) else (
    echo 服务未启动，请先选择“2”。
)
pause
goto menu

:end
popd
endlocal
exit /b 0
