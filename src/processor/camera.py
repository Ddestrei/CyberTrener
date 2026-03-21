import cv2
import threading
import time
import atexit
import glob
import re
import os
import platform  # To detect the operating system

# [LOCK] Global hardware lock.
# Prevents "Device Busy" (Linux) and access conflicts (Windows) 
# when two threads attempt to initialize a camera simultaneously.
hardware_lock = threading.Lock()

# Check system type once at startup.
# This allows selecting the appropriate OpenCV video backend.
IS_WINDOWS = (platform.system() == 'Windows')

class VideoThread(threading.Thread):
    """
    Thread class handling continuous camera reading in the background.
    Runs independently of the main UI loop to prevent interface freezing.
    """
    def __init__(self, src, name="Camera"):
        super().__init__()
        self.src = src  # Device ID (e.g., 0, 1)
        self.name = name
        self.capture = None
        self.frame = None
        self.online = False
        self.error_msg = None 
        self._stop_event = threading.Event()
        self.daemon = True # Thread dies automatically when the app closes

    def run(self):
        """Main thread loop: initialization and frame acquisition."""
        with hardware_lock:
            # [CROSS-PLATFORM] Video backend selection
            if IS_WINDOWS:
                print(f"[{self.name}] Initializing CAM {self.src} (Windows DSHOW)...")
                # On Windows, DirectShow is the fastest/standard standard
                backend = cv2.CAP_DSHOW
            else:
                print(f"[{self.name}] Initializing /dev/video{self.src} (Linux V4L2)...")
                # On Linux (Arch/Ubuntu), Video4Linux2 is the standard
                backend = cv2.CAP_V4L2

            # Attempt to open camera with the selected driver
            self.capture = cv2.VideoCapture(self.src, backend)
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            
            # [PERFORMANCE] Video stream configuration.
            # 1. Force VGA resolution (640x480).
            #    Two HD cameras on one USB controller often exceed bandwidth.
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.capture.set(cv2.CAP_PROP_FPS, 60)
            
            # 2. [LATENCY] Set buffer size to 1 frame.
            #    Crucial setting! Tells the driver not to queue old frames.
            #    Ensures we always see "live" video rather than delayed footage.
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.capture.isOpened():
                self.error_msg = "Could not open (Busy/Missing)"
                print(f"[{self.name}] ERROR: {self.error_msg}")
                
                # Hint for Linux users only (Windows doesn't use modprobe)
                if not IS_WINDOWS and self.src >= 2:
                    print(f"[{self.name}] HINT: Check v4l2loopback (exclusive_caps=1)")
                
                self.online = False
                return

            self.online = True
            self.error_msg = None
            print(f"[{self.name}] START (Online).")

        # Read loop (runs until the thread is stopped)
        while not self._stop_event.is_set():
            if not self.capture.isOpened():
                self.online = False
                break
            
            ret, frame = self.capture.read()
            if ret:
                # Mirroring - provides a more natural experience for the user
                self.frame = cv2.flip(frame, 1)
            else:
                # Short rest if no frame is returned (e.g., camera initializing)
                time.sleep(0.01)
            
            # [CPU SAVER] Micro-sleep to prevent the thread from consuming 100% of a CPU core
            time.sleep(0.005)

        self._release()

    def _release(self):
        """Safely release camera resources."""
        with hardware_lock:
            if self.capture and self.capture.isOpened():
                self.capture.release()
            self.online = False
            print(f"[{self.name}] Stopped.")

    def get_frame(self, resize_width=None):
        """
        Returns a copy of the latest frame.
        Supports resizing BEFORE sending to the UI, which drastically increases FPS.
        """
        if self.frame is not None:
            f = self.frame.copy()
            if resize_width:
                # Aspect ratio-preserving scaling:
                # $$aspect = \frac{height}{width}$$
                h, w = f.shape[:2]
                aspect = h / w
                new_h = int(resize_width * aspect)
                f = cv2.resize(f, (resize_width, new_h), interpolation=cv2.INTER_NEAREST)
            return f
        return None

    def stop(self):
        """Signal the thread to stop."""
        self._stop_event.set()
        if self.is_alive():
            self.join(timeout=1.0)
        # Fallback: force release resources if the thread hangs
        if self.capture and self.capture.isOpened():
            self._release()

class CameraManager:
    """
    Manager class handling cameras across different operating systems.
    Should be used as a Singleton (one instance per application).
    """
    def __init__(self):
        self.active_threads = {} # Dictionary of active threads: {'front': Thread, ...}
        atexit.register(self.stop_all) # Ensure cleanup when the program exits

    def passive_scan(self):
        """
        [DISCOVERY] Detection of available cameras.
        Behavior differs by system for safety reasons.
        """
        print(f"[Manager] Scanning ({platform.system()})...")
        self.stop_all() # Reset before scanning
        time.sleep(0.5)
        
        candidates = []

        if IS_WINDOWS:
            # [WINDOWS] Scanning ports in a loop on Windows often freezes OpenCV.
            # It's safer to provide the user with a range of IDs (0-3).
            # The user can select the correct camera via trial and error.
            candidates = [0, 1, 2, 3]
        else:
            # [LINUX] We can safely check files in /dev/video*
            try:
                files = sorted(glob.glob('/dev/video*'))
                for f in files:
                    if os.access(f, os.R_OK):
                        match = re.search(r'video(\d+)', f)
                        if match:
                            candidates.append(int(match.group(1)))
            except Exception:
                candidates = [0, 1, 2]

            # Fallback: always add typical ports for OBS/DroidCam (e.g., 20)
            for force_id in [0, 1, 2, 20]:
                if force_id not in candidates and os.path.exists(f"/dev/video{force_id}"):
                    candidates.append(force_id)

        candidates = sorted(list(set(candidates)))
        print(f"[Manager] Available slots: {candidates}")
        return candidates

    def start_camera(self, role, src):
        """Starts a camera (src) for a given role (role)."""
        curr = self.active_threads.get(role)
        
        # If the thread is already running correctly - do not restart it
        if curr and curr.is_alive() and curr.src == src and curr.online:
            return

        # If the source changes - stop the old thread
        if curr:
            curr.stop()
        
        # Start a new thread
        t = VideoThread(src, role)
        t.start()
        self.active_threads[role] = t
        time.sleep(0.2) # Hardware initialization time

    def get_frame(self, role, resize_width=None):
        t = self.active_threads.get(role)
        if t and t.online:
            return t.get_frame(resize_width)
        return None
    
    def get_status(self, role):
        """Returns error message if the camera is not working."""
        t = self.active_threads.get(role)
        if t and not t.online and t.error_msg:
            return t.error_msg
        return None

    def stop_role(self, role):
        """Stops the camera only for one role (e.g., Side)."""
        t = self.active_threads.get(role)
        if t:
            t.stop()
            del self.active_threads[role]

    def stop_all(self):
        """Stops all active cameras."""
        # [FIX] Copy the list of values to avoid:
        # "RuntimeError: dictionary changed size during iteration"
        threads_to_stop = list(self.active_threads.values())
        
        for t in threads_to_stop:
            t.stop()
        
        self.active_threads.clear()