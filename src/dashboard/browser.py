import threading
import time
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

class EdgeLauncherThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self.driver = None

    def stop(self):
        self._stop_event.set()
        if self.driver:
            self.driver.quit()
        print("EdgeLauncherThread stopped.")

    def run(self):
        print("Starting EdgeLauncherThread...")
        self.driver = webdriver.Edge()  # Assumes Edge WebDriver is correctly installed and in PATH
        self.driver.maximize_window()
        
        while not self._stop_event.is_set():
            try:
                self.driver.get("http://127.0.0.1:8050/")
                print("Successfully navigated to http://127.0.0.1:8050/")
                break
            except WebDriverException as e:
                print(f"Navigation failed: {e}. Retrying in 1 second...")
                time.sleep(1)
        
        while not self._stop_event.is_set():
            time.sleep(1)