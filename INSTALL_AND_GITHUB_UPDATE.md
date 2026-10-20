# Laptop Doctor — install, test, and update GitHub

This package contains the complete source project. It does not contain a prebuilt Windows EXE; GitHub Actions builds that on a Windows runner after the source is updated.

## A. Run from source on Windows 10/11

1. Install Python 3.12 from https://www.python.org/downloads/windows/ if it is not installed. During setup, enable **Add python.exe to PATH**.
2. Extract this ZIP to a normal folder, for example `C:\Users\Lenovo\Downloads\LaptopDoctor`.
3. Open PowerShell in that extracted `LaptopDoctor` folder.
4. Run these commands one at a time:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py
```

The expected automated-test result is `OK`. If `python` is not recognized, install Python and make sure **Add python.exe to PATH** is selected, then reopen PowerShell. This package deliberately does not require the `py` launcher.

You can also double-click `setup.bat` to install dependencies, then run `build.bat` to build locally. GitHub Actions is the recommended EXE build route.

## B. Add a whole-drive scan

1. Open Laptop Doctor and go to **Settings**.
2. Under **Read-only scan locations**, add `C:\` and save settings.
3. Keep **Folders allowed for cleanup** limited to specific folders inside your home folder, for example `C:\Users\Lenovo\Downloads` or a dedicated test folder.

A scan location is read-only inventory permission, not cleanup permission. Only files under cleanup-approved folders can be proposed for changes. Windows may deny access to some locations; these are skipped. Scanning is capped at 200,000 files per run and can be partial on very large drives. Test changes with disposable files first.

## C. Update the existing GitHub repository using the browser

Repository: https://github.com/Baichau/LaptopDoctor

GitHub cannot unpack this ZIP into the repository automatically. You can update files entirely in the browser:

1. Download and extract this ZIP on your PC so you can open the files in a text editor.
2. Open the repository link above. For each file in the list below, navigate to that exact file, click the pencil **Edit** button, replace the entire contents with the corresponding file from this extracted package, then commit the change to `main`.
3. Add the new `GITHUB_BROWSER_UPDATE.md` file at the repository root using **Add file → Create new file**.
4. Do not upload `.venv`, `.git`, `dist`, `build`, cache files, private files, or the ZIP itself into the repository.

Replace these files from this ZIP, preserving their paths:

- `laptop_doctor/server.py`
- `laptop_doctor/web/app.js`
- `tests/test_core.py`
- `README.md`
- `E2E_TESTING.md`
- `PUBLISHING.md`

Add this new file:

- `GITHUB_BROWSER_UPDATE.md`

The `.github/workflows/windows-build.yml`, `main.py`, `requirements*.txt`, `setup.bat`, `build.bat`, CSS and HTML files do not need changes for this update.

## D. Build and release the EXE

1. On GitHub, open **Actions**: https://github.com/Baichau/LaptopDoctor/actions
2. Open the latest **Windows tests and executable** run. Each push to `main` should start a new run.
3. Wait for the green checkmark. If it fails, open the failed step and fix that before sharing.
4. On the run summary, find **Artifacts** and download `LaptopDoctor-Windows-x64`.
5. Extract the artifact and test `LaptopDoctor.exe` on Windows, ideally on a computer without Python installed.
6. Only after manual testing passes, create a GitHub Release and attach `LaptopDoctor.exe` as a release asset. Share the release page, not the source ZIP.

## E. Required safety checks before sharing

- All automated tests pass in GitHub Actions.
- `C:\` can be saved as a scan location.
- Scanning does not move or delete files.
- Files outside cleanup-approved folders are not actionable.
- User-confirmed test-file changes move as expected and Undo restores them.
- The EXE starts on a Windows computer without Python.
- Ollama is optional; the EXE does not bundle Ollama or a model.
- Windows SmartScreen may warn because the EXE is unsigned. Do not tell friends to blindly bypass warnings.
