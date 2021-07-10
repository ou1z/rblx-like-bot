import subprocess, time, win32ui, win32gui, win32con, win32process
from PIL import Image

def get_hwnd_for_pid(pid: int) -> int:
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True
        
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds and hwnds[0]

class Client:
    def __init__(self, client_path, auth_ticket, join_script_url,
                 browser_tracker_id, locale):
        self.client_path = client_path
        self.auth_ticket = auth_ticket
        self.join_script_url = join_script_url
        self.browser_tracker_id = browser_tracker_id
        self.locale = locale
        self._process = None
        self.hwnd = None

    def __del__(self):
        self.close()
        super().__init__()

    @property
    def pid(self):
        if self._process:
            return self._process.pid

    def start(self):
        """Launches client process."""
        if self._process:
            return

        self._process = subprocess.Popen([
            self.client_path,
            "-t", self.auth_ticket,
            "-j", self.join_script_url,
            "-b", self.browser_tracker_id,
            f"--launchtime={time.time()*1000:0.0f}",
            "--rloc", self.locale,
            "--gloc", self.locale
        ])

        start = time.time()
        while time.time()-start < 15:
            hwnd = get_hwnd_for_pid(self._process.pid)
            if hwnd:
                self.hwnd = hwnd
                break
            
    def wait(self, timeout=None):
        """Blocks until client process is closed."""
        self._process.wait(timeout)

    def close(self, force=False):
        """Terminates client process."""
        if not self._process:
            return
            
        if force:
            self._process.kill()
        else:
            self._process.terminate()
            
    def wait_for(self, timeout: float=15, check_interval: float=0.25,
        ignored_colors: list=[(45, 45, 45), (255,255,255), (0, 0, 0)]):
        start = time.time()
        
        while time.time()-start < timeout:
            screenshot = self.screenshot()
            px_count = screenshot.size[0]*screenshot.size[1]
            dominant_color = sorted(
                screenshot.getcolors(px_count),
                key=lambda t: t[0])[-1][1]

            if not dominant_color in ignored_colors:
                return True
            time.sleep(check_interval)
        
        return False
    
    def size(self, xo=0, yo=0) -> tuple:
            rect = win32gui.GetWindowRect(self.hwnd)
            x = rect[0]
            y = rect[1]
            w = rect[2] - x
            h = rect[3] - y
            return (w-xo, h-yo)

    def screenshot(self, crop=True) -> Image:
        dc_handle = win32gui.GetWindowDC(self.hwnd)
        dcObj=win32ui.CreateDCFromHandle(dc_handle)
        cDC=dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, *self.size())
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0,0),self.size(), dcObj, (0,0), win32con.SRCCOPY)
        bmpinfo = dataBitMap.GetInfo()
        bmpstr = dataBitMap.GetBitmapBits(True)
        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.DeleteObject(dataBitMap.GetHandle())
        win32gui.ReleaseDC(self.hwnd, dc_handle)
        if crop:
            im = im.crop((11,45, *self.size(11, 11)))
        return im