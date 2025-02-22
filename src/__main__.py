import keyboard
from .utils import kill_python_processes

from .dashboard import app, EdgeLauncherThread

def main():
    def CtrlShiftC_handler():
        print("\nYou pressed Ctrl+shift+C! Shutting down gracefully...")
        print("Exiting...")
        kill_python_processes()        
        exit(0)


    # Attach the signal handler for forced shutdown
    keyboard.add_hotkey("ctrl+shift+c", CtrlShiftC_handler)

    print("Starting Dashboard...")
    print("Press Ctrl+Shift+C to stop the program.")
    browser = EdgeLauncherThread()
    browser.start()
    app.run_server(debug=False)

if __name__ == '__main__':
    main()