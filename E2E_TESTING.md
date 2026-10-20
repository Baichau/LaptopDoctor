# Laptop Doctor — end-to-end testing

Run these checks **before sharing a build**. The automated tests use a temporary fake home directory; they do not clean or modify your real Downloads folder.

## 1. Automated tests (required)

Open PowerShell in the repository folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected result: all tests pass. Do not publish if a test fails.

## 2. Run the source version

```powershell
.\.venv\Scripts\python.exe main.py
```

The app should open in a desktop window. If the native window is unavailable, it should open in your browser. To force browser mode:

```powershell
$env:LD_BROWSER = '1'
.\.venv\Scripts\python.exe main.py
```

## 3. Safe manual smoke test

1. Create a temporary folder such as `%USERPROFILE%\LaptopDoctor-Test` and put a few **disposable test files** in it: `picture.jpg`, `notes.txt`, and a file larger than 1 MB copied twice.
2. In Settings, add only that test folder. Do not enable cache cleanup for this test.
3. Run analysis. Confirm that files changed in the last two days are not suggested and nothing is selected automatically.
4. Select one harmless suggestion and apply it. Confirm it moves to a category folder or the app's quarantine, rather than being deleted.
5. Open History and use **Undo batch**. Confirm the file returns to its original location.
6. Restart the app and confirm Settings and History persist.
7. Test with Ollama stopped or no model selected. The app should still show rule-based suggestions and an AI error notice, not crash.
8. Close and reopen the app; check that it binds to localhost and the UI loads.
9. Delete the test folder yourself after verifying its contents. Do not use real files as test data.

## 4. Test the packaged EXE

Build with `build.bat`, or download `LaptopDoctor.exe` from the GitHub Actions artifact. Run the EXE on a Windows machine that does not have the repository or Python installed. Confirm the same startup, analysis, review, apply, undo, and restart checks work.

The EXE does not include Ollama or an AI model. For AI advice, each user must install Ollama and download a model; rule-based scanning still works without it.
