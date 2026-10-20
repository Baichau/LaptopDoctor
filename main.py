"""Entry point. Run: python main.py   (set LD_BROWSER=1 to use your browser + DevTools instead of the native window)"""
import os, threading, webbrowser
from laptop_doctor import server


def run():
    url = server.serve()
    if not os.environ.get("LD_BROWSER"):
        try:
            import webview  # native window
            webview.create_window("Laptop Doctor", url, width=1100, height=780, min_size=(380, 560))
            webview.start()
            return
        except Exception:
            pass
    webbrowser.open(url)
    threading.Event().wait()


if __name__ == "__main__":
    run()
