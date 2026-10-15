@echo off
REM Genera dist\PortalArquitecto\PortalArquitecto.exe  (comprime la carpeta dist\PortalArquitecto para distribuir)
cd /d "%~dp0"

if not exist .venv-build (
    python -m venv .venv-build || goto :error
)
call .venv-build\Scripts\activate.bat
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt || goto :error

python -m PyInstaller --noconfirm --clean PortalArquitecto.spec || goto :error

echo.
echo Listo: dist\PortalArquitecto\PortalArquitecto.exe
echo Los modelos del usuario se guardan en %%LOCALAPPDATA%%\PortalArquitecto\modelos_vr
exit /b 0

:error
echo Error durante la compilacion.
exit /b 1

