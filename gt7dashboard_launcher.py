"""GT7 Dashboard Launcher

Starts the Bokeh server and opens the dashboard in a browser.
This script is the entry point when the app is packaged as a Windows
executable with PyInstaller.

Usage (script):
    python gt7dashboard_launcher.py

Usage (exe, after building with PyInstaller):
    gt7dashboard.exe
"""

import os
import sys
import threading
import time
import webbrowser


def ask_playstation_ip():
    """Show a GUI dialog asking for the PlayStation IP address."""
    try:
        import tkinter as tk
        from tkinter import simpledialog

        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes("-topmost", True)

        ip = simpledialog.askstring(
            "GT7 Dashboard \u2013 Setup",
            "Enter your PlayStation IP address.\n\n"
            "Find it on your PS5 at:\n"
            "Settings \u2192 Network \u2192 View Connection Status\n\n"
            "Leave empty to use automatic discovery\n"
            "(recommended for most home networks):",
            parent=root,
        )
        root.destroy()
        if ip and ip.strip():
            return ip.strip()
    except Exception:
        pass
    return "255.255.255.255"


def main():
    # ---- Determine directories ----
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle.
        # Bundled files (main.py, gt7dashboard/) live in sys._MEIPASS.
        app_dir = sys._MEIPASS
        # Change to the exe's own directory so saved laps end up there,
        # not in the temporary extraction folder.
        os.chdir(os.path.dirname(sys.executable))
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))

    # Ensure the data directory exists so saving/loading laps works.
    os.makedirs(os.path.join(os.getcwd(), "data"), exist_ok=True)

    # ---- PlayStation IP ----
    if not os.environ.get("GT7_PLAYSTATION_IP"):
        os.environ["GT7_PLAYSTATION_IP"] = ask_playstation_ip()

    # ---- Start Bokeh server ----
    from bokeh.application import Application
    from bokeh.application.handlers.directory import DirectoryHandler
    from bokeh.server.server import Server

    handler = DirectoryHandler(filename=app_dir)
    bokeh_app = Application(handler)

    port = 5006
    server = Server({"/": bokeh_app}, port=port)
    server.start()

    url = f"http://localhost:{port}"

    def _open_browser():
        time.sleep(2)
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()

    print(f"GT7 Dashboard is running at {url}")
    print("The dashboard will open in your browser automatically.")
    print("Keep this window open while using the dashboard.")
    print("Press Ctrl+C to stop.")

    try:
        server.io_loop.start()
    except KeyboardInterrupt:
        print("\nStopping GT7 Dashboard...")
        server.stop()


if __name__ == "__main__":
    main()
