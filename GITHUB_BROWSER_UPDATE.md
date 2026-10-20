# Update Laptop Doctor using only the GitHub website

This update separates **read-only scan locations** from **cleanup-approved folders**. It allows a scan location such as `C:\` without granting permission to move files outside your approved user folders.

## Important

- Do not replace only `server.py` with an unrelated version. Update all files listed below together.
- GitHub does not unpack a ZIP into a repository. Use the browser editor to replace each file, or use the repository's `.` editor if available.
- Do not enable cleanup of `C:\`, `C:\Windows`, `C:\Program Files`, or other protected locations. This app intentionally does not permit those locations as cleanup roots.
- This app is not independently security-audited. Test with disposable files before using cleanup.

## Files to replace in your existing repository

From the extracted `LaptopDoctor` folder in this ZIP, replace these existing files on GitHub, keeping their exact paths:

1. `laptop_doctor/server.py`
2. `laptop_doctor/web/app.js`
3. `tests/test_core.py`
4. `README.md`
5. `E2E_TESTING.md`
6. `PUBLISHING.md`

Add this new file at the repository root:

7. `GITHUB_BROWSER_UPDATE.md`

Other project files are unchanged. Do not upload `.venv`, `.git`, `dist`, caches, personal files, or the ZIP itself into the repository.

## Browser workflow

1. Open https://github.com/Baichau/LaptopDoctor.
2. Open a file listed above and use the pencil (Edit) control.
3. In the ZIP you downloaded, open the matching file in a text editor and copy its full contents.
4. Replace the entire GitHub editor contents, preview the diff, and commit to `main`. Repeat for the other files. For the new Markdown file, choose **Add file → Create new file** and name it `GITHUB_BROWSER_UPDATE.md`.
5. Wait for **Actions → Windows tests and executable** to finish. Do not distribute the EXE unless the workflow passes.
6. Download the `LaptopDoctor-Windows-x64` artifact from the successful run, extract it, and test the EXE before creating a release.

## Configure whole-drive inventory

In the app, open **Settings → Read-only scan locations**, add `C:\`, and save. Keep **Folders allowed for cleanup** restricted to a specific user folder such as `C:\Users\Lenovo\Downloads` or a dedicated test folder. A whole-drive scan inventories accessible files, but only files under cleanup-approved folders can be proposed for moves. Windows-protected locations may be skipped. The inventory has a 200,000-file cap and may be partial on very large drives.

## Test expectations

The automated tests run in GitHub Actions on Windows. Manually verify that:

- `C:\` can be saved as a scan location.
- Scanning does not move or delete anything.
- Only items inside cleanup-approved folders are offered as actionable changes.
- Items outside approved folders cannot be moved by submitting crafted IDs.
- Undo restores approved test-file changes.
- The EXE starts on a Windows account without Python installed.
