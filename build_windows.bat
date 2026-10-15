@echo off
REM Genera dist\RooSpatialPortal\RooSpatialPortal.exe
cd /d "%~dp0"

if not exist .venv-build (
    python -m venv .venv-build || goto :error
)
call .venv-build\Scripts\activate.bat
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt || goto :error

python -m PyInstaller --noconfirm --clean PortalArquitecto.spec || goto :error

echo.
echo ========================================================
echo  Compilacion exitosa: dist\RooSpatialPortal\RooSpatialPortal.exe
echo  Desarrollado por roo Soluciones Digitales
echo  Los datos de modelos se alojan en:
echo  %%LOCALAPPDATA%%\RooSpatialPortal\modelos_vr
echo ========================================================
exit /b 0

:error
echo Error durante la compilacion.
exit /b 1

