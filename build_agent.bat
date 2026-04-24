@echo off
setlocal
echo ========================================
echo  I-Dashboard Agent - Windows 빌드
echo ========================================

echo [1/3] 의존성 설치...
pip install pyinstaller psutil python-dotenv rich
if errorlevel 1 goto :error

echo [2/3] PyInstaller로 exe 빌드...
pyinstaller ^
  --onefile ^
  --name i-dashboard-agent ^
  --hidden-import psutil ^
  --hidden-import psutil._pswindows ^
  --hidden-import dotenv ^
  --collect-submodules core ^
  agent/main.py
if errorlevel 1 goto :error

echo [3/3] 완료!
echo.
echo 실행파일: dist\i-dashboard-agent.exe
echo.
echo 사용법:
echo   set BACKEND_URL=http://백엔드서버IP:8000
echo   set AGENT_TOKEN=설정한-토큰
echo   dist\i-dashboard-agent.exe
echo.
echo 또는 .env 파일에 위 변수를 설정하고 실행
goto :end

:error
echo.
echo 빌드 실패. 오류를 확인하세요.
exit /b 1

:end
endlocal
