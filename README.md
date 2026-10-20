# Laptop Doctor

Laptop Doctor is a Windows-first desktop utility that helps review clutter in folders you explicitly allow. It identifies possible duplicate files, loose files that could be sorted into category folders, old large files, and (optionally) user cache items. You review every suggestion and select each change yourself.

**Safety-first behavior:** the app does not permanently delete files. Selected items are moved into category folders or a quarantine folder, and applied batches are recorded for Undo. Always test with disposable files first.

## Features

- Local desktop UI with a browser fallback.
- Rule-based scanning that works without an AI model.
- Optional AI advice from a local [Ollama](https://ollama.com/) server; filenames and a limited summary are sent to the local model, not a cloud AI service.
- Review-first changes: nothing is preselected.
- Quarantine instead of permanent deletion, plus batch undo.
- Separate read-only scan locations from cleanup-approved folders.
- Whole-drive inventory support (for example `C:\`) without granting cleanup permission outside explicitly approved user folders.
- Permission-denied paths are skipped; inventory is capped at 200,000 files per run and can therefore be partial on very large drives.

## Requirements

- Windows 10/11 recommended.
- Python 3.12 for running from source or building locally.
- Optional: Ollama plus a locally downloaded model for AI advice. The EXE does **not** bundle Ollama or a model.

## Run from source

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
```

Or run `setup.bat`, then open the project in VS Code. Use `LD_BROWSER=1` to force browser mode.

## Test

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

See [E2E_TESTING.md](E2E_TESTING.md) for automated and manual end-to-end checks.

## Build the Windows EXE

On Windows, run `setup.bat` and then `build.bat`. The executable is created at `dist\LaptopDoctor.exe`.

A GitHub Actions workflow also runs tests and builds the EXE on Windows. See [PUBLISHING.md](PUBLISHING.md) for the clean-repository, Actions artifact, and GitHub Release workflow. If you only have GitHub browser access, follow [GITHUB_BROWSER_UPDATE.md](GITHUB_BROWSER_UPDATE.md) to update the existing repository. See [INSTALL_AND_GITHUB_UPDATE.md](INSTALL_AND_GITHUB_UPDATE.md) for complete installation and release instructions. Share the release's EXE asset with friends; do not send them the source project unless they want it.

## Data and privacy

Configuration, action history, quarantine, and windowed-build logs are stored under `%USERPROFILE%\.laptop_doctor`. The server binds to localhost. Scan locations can include `C:\` and are inventoried read-only; hidden entries and directory symlinks are skipped, and permission errors are ignored. A run is capped at 200,000 files and may be partial. Only explicitly approved folders strictly inside the user's home directory are eligible for changes. Files changed within the last two days are not proposed. Cloud-synced folders may synchronize file moves to other devices.

## Important limitations

- The executable is unsigned, so Windows SmartScreen or antivirus may warn. Never bypass warnings without verifying the file and source.
- AI advice requires Ollama to be installed and running separately.
- This is a file organizer, not a complete laptop health or malware diagnostic tool.
- The app has not been independently security-audited. Use the manual test checklist and keep backups of important data.
