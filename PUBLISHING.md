# Publish Laptop Doctor to GitHub and share the EXE

## A. Create a clean GitHub repository

1. Create a **public** repository on GitHub named `LaptopDoctor` (or another name). Do not initialize it with a README, license, or `.gitignore` because those files are already in this project.
2. Extract the source ZIP and open PowerShell in the extracted `LaptopDoctor` folder.
3. Check that `.venv`, `dist`, `build`, `__pycache__`, and personal app data are not included. The `.gitignore` excludes them; the original ZIP should not be uploaded as-is because it contained a virtual environment.
4. Initialize and push:

```powershell
git init
git add .
git status
git commit -m "Prepare Laptop Doctor for public release"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/LaptopDoctor.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. Review `git status` before committing and make sure no private files or tokens are staged.

## B. Build the EXE on GitHub (recommended)

The repository includes `.github/workflows/windows-build.yml`. GitHub Actions builds on Windows, runs the tests, and uploads `LaptopDoctor.exe` as an artifact.

1. On GitHub, open **Actions** and select **Windows tests and executable**.
2. Wait for the run to finish green.
3. Open the run and download the artifact named `LaptopDoctor-Windows-x64`. Unzip it to get `LaptopDoctor.exe`.
4. Test that EXE on a Windows PC, ideally one without Python installed, before sharing.

You can also build locally on Windows by running `setup.bat`, then `build.bat`. The output is `dist\LaptopDoctor.exe`. The build script pauses at the end, so it is intended for an interactive terminal.

## C. Publish a versioned release

1. In GitHub, open **Releases → Draft a new release**.
2. Create a tag such as `v1.0.0`, add concise release notes, and attach `LaptopDoctor.exe` (not the source project ZIP).
3. Publish the release. GitHub will also provide its automatically generated source-code archives.
4. Send friends the release page URL. They can download the EXE under **Assets**.

## D. What to tell friends

- This is a Windows desktop app. It does not require them to install Python.
- AI advice requires Ollama and a downloaded model; otherwise the rule-based suggestions can still run.
- The app is unsigned, so Windows SmartScreen or antivirus may warn. Do not tell people to bypass a warning blindly. Share the public source repository so they can inspect the code, and consider code signing before a broad public release.
- The app can move files after the user selects and confirms actions. Encourage first-time users to test with a disposable folder and verify Undo before using it on real files.

## E. Before public release

- Run all tests and complete the manual checklist in `E2E_TESTING.md`.
- Add a license only if you are comfortable choosing the terms under which others may reuse your code. No license is added automatically here.
- Confirm you own or have permission to publish all code and assets.
- Review GitHub's repository visibility and the contents of every commit. `.gitignore` does not remove files already committed in earlier commits.
