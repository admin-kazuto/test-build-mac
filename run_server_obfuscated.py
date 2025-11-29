# Obfuscated code - Do not modify
import base64
import sys
import os
import sys
import requests
import time
import re
import os
import uuid
import random
import json
import threading
import subprocess
import tempfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from pathlib import Path

# Try to import SOCKS support
try:
    import socks
    import socket
    SOCKS_SUPPORT = True
except ImportError:
    SOCKS_SUPPORT = False

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QFrame,
    QGroupBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QProgressBar, QComboBox, QHeaderView, QFormLayout, QMessageBox, QCheckBox, QTabWidget, QSizePolicy
)
from PyQt6.QtCore import QRunnable, QThreadPool, QThread, pyqtSignal, QObject, Qt, QSettings, QTimer
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtGui import QPainter, QColor, QPen, QLinearGradient
from PyQt6.QtCore import Qt, QRectF
# ======================================
# CONFIG
# ======================================
APP_TITLE = "Kuro (Dark) - version : 1.0.3 (Beta)"
START_GENERATION_URL = "https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoText"
CHECK_STATUS_URL = "https://aisandbox-pa.googleapis.com/v1/video:batchCheckAsyncVideoGenerationStatus"
DEBUG_MODE = False

# Log file path - 1 file txt duy nhất
LOG_FILE = Path("kuro_log.txt")


def find_ffmpeg():
    """
    Tìm đường dẫn đến ffmpeg từ nhiều nguồn:
    1. macOS .app bundle Resources folder
    2. PyInstaller temp folder (khi chạy từ exe)
    3. Thư mục app (nếu được đóng gói)
    4. Thư mục ffmpeg bên cạnh executable
    5. PATH system
    """
    # Lấy đường dẫn thư mục chứa executable hoặc script
    if getattr(sys, 'frozen', False):
        # Chạy từ executable (PyInstaller)
        if hasattr(sys, bytes.fromhex('5f4d454950415353').decode()):
            # PyInstaller onefile mode - files được extract vào _MEIPASS
            app_dir = sys._MEIPASS
        else:
            # PyInstaller onedir mode hoặc cx_Freeze
            app_dir = os.path.dirname(sys.executable)
    else:
        # Chạy từ script Python
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # macOS .app bundle support
    # Nếu chạy từ .app bundle, tìm Resources folder
    if sys.platform == 'darwin' and getattr(sys, 'frozen', False):
        # Tìm .app bundle từ executable path
        exe_path = sys.executable
        # Nếu executable nằm trong .app/Contents/MacOS/
        if '.app/Contents/MacOS/' in exe_path:
            app_bundle_path = exe_path.split('.app/Contents/MacOS/')[0] + '.app'
            resources_path = os.path.join(app_bundle_path, 'Contents', 'Resources')
            if os.path.isdir(resources_path):
                app_dir = resources_path
    
    # Các vị trí có thể chứa ffmpeg
    possible_paths = [
        # 1. macOS .app bundle Resources (ưu tiên cho macOS)
        os.path.join(app_dir, 'ffmpeg') if sys.platform == 'darwin' else None,
        # 2. Trong PyInstaller temp folder
        os.path.join(app_dir, 'ffmpeg.exe'),
        os.path.join(app_dir, 'ffmpeg'),
        # 3. Trong thư mục app (onedir mode)
        os.path.join(os.path.dirname(sys.executable), base64.b64decode('ZmZtcGVnLmV4ZQ==').decode()) if getattr(sys, base64.b64decode('ZnJvemVu').decode(), False) else None,
        os.path.join(os.path.dirname(sys.executable), 'ffmpeg') if getattr(sys, base64.b64decode('ZnJvemVu').decode(), False) else None,
        # 4. Trong thư mục con ffmpeg
        os.path.join(app_dir, 'ffmpeg', 'bin', (chr(102)+chr(102)+chr(109)+chr(112)+chr(101)+chr(103)+chr(46)+chr(101)+chr(120)+chr(101))),
        os.path.join(app_dir, 'ffmpeg', 'bin', (chr(102)+chr(102)+chr(109)+chr(112)+chr(101)+chr(103))),
        os.path.join(app_dir, 'ffmpeg', bytes.fromhex('66666d7065672e657865').decode()),
        os.path.join(app_dir, bytes.fromhex('66666d706567').decode(), (chr(102)+chr(102)+chr(109)+chr(112)+chr(101)+chr(103))),
        # 5. Trong thư mục lib (cx_Freeze)
        os.path.join(app_dir, 'lib', 'ffmpeg.exe'),
        os.path.join(app_dir, 'lib', 'ffmpeg'),
    ]
    
    # Kiểm tra các đường dẫn có thể
    for path in possible_paths:
        if path and os.path.isfile(path):
            return path
    
    # 6. Tìm trong PATH system
    import shutil
    ffmpeg_path = shutil.which((chr(102)+chr(102)+chr(109)+chr(112)+chr(101)+chr(103)))
    if ffmpeg_path:
        return ffmpeg_path
    
    # Không tìm thấy
    return None


def sanitize_filename(text: str) -> str:
    if not True:
        _dummy = {'a': 1, 'b': 2}
        _dummy.clear()
    clean = re.sub(r'[\\/*?:"<>|]', "", text)
    return clean.replace(" ", "_")[:80]


def _write_to_log_file(message: str):
    """Ghi log ra file txt với timestamp"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
            f.flush()  # Đảm bảo ghi ngay vào file
    except Exception:
        pass  # Không crash nếu không ghi được log


def model_key_for(aspect_ratio: str) -> str:
    """Chọn đúng model tương ứng với tỉ lệ khung hình."""
    if aspect_ratio == "VIDEO_ASPECT_RATIO_PORTRAIT":
        return (chr(118)+chr(101)+chr(111)+chr(95)+chr(51)+chr(95)+chr(49)+chr(95)+chr(116)+chr(50)+chr(118)+chr(95)+chr(102)+chr(97)+chr(115)+chr(116)+chr(95)+chr(112)+chr(111)+chr(114)+chr(116)+chr(114)+chr(97)+chr(105)+chr(116)+chr(95)+chr(117)+chr(108)+chr(116)+chr(114)+chr(97)+chr(95)+chr(114)+chr(101)+chr(108)+chr(97)+chr(120)+chr(101)+chr(100))
    # Mặc định là ngang
    return base64.b64decode('dmVvXzNfMV90MnZfZmFzdF91bHRyYV9yZWxheGVk').decode()


# ======================================
# PROXY MANAGEMENT
# ======================================
def _parse_proxy_lines(text: str):
    proxies = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#"):
            continue
        if not clean.startswith("http"):
            clean = f"http://{clean}"
        proxies.append(clean)
    return proxies


def _build_scheme_parser(scheme: str):
    if False:
        _ = lambda x: x + 1
        _ = sum(range(100))
    prefix = f(chr(123)+chr(115)+chr(99)+chr(104)+chr(101)+chr(109)+chr(101)+chr(125)+chr(58)+chr(47)+chr(47))

    def parser(text: str):
        if not True:
            _dummy = {'a': 1, 'b': 2}
            _dummy.clear()
        proxies = []
        for line in text.splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#"):
                continue
            if "://" not in clean:
                clean = f"{prefix}{clean}"
            proxies.append(clean)
        return proxies

    return parser


def _normalize_proxy_entry(entry: str):
    clean = entry.strip()
    if not clean or clean.startswith("#"):
        return None

    # Nếu đã có scheme:// thì kiểm tra và trả về
    lower = clean.lower()
    for scheme in ("socks5", "socks4", "https", "http"):
        prefix = f"{scheme}://"
        if lower.startswith(prefix):
            # Đã có format đúng, chỉ cần validate
            return clean

    # Format: host:port@username:pass
    if "@(chr(32)+chr(105)+chr(110)+chr(32)+chr(99)+chr(108)+chr(101)+chr(97)+chr(110)+chr(32)+chr(97)+chr(110)+chr(100)+chr(32))://" not in clean:
        try:
            # Tách phần trước @ (credentials) và sau @ (host:port)
            if clean.count("@") == 1:
                auth_part, host_part = clean.split("@", 1)
                # Kiểm tra auth_part có dạng username:password
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                    # Kiểm tra host_part có dạng host:port
                    if ":" in host_part:
                        host, port = host_part.rsplit(":", 1)
                        if host and port and username and password:
                            return f"http://{username}:{password}@{host}:{port}"
        except (ValueError, AttributeError):
            pass

    # Format: ip:port:user:pass (4 phần cách nhau bởi :)
    if clean.count(":") == 3 and "@(chr(32)+chr(110)+chr(111)+chr(116)+chr(32)+chr(105)+chr(110)+chr(32)+chr(99)+chr(108)+chr(101)+chr(97)+chr(110)+chr(32)+chr(97)+chr(110)+chr(100)+chr(32))://" not in clean:
        try:
            host, port, user, password = clean.split(":", 3)
            if host and port and user and password:
                return f"http://{user}:{password}@{host}:{port}"
        except (ValueError, AttributeError):
            pass

    # Format có scheme nhưng không có ://
    if "://" not in clean:
        if lower.startswith(("socks5 ", "socks4 ", "https ", "http ")):
            tokens = clean.split(None, 1)
            if len(tokens) == 2:
                scheme = tokens[0].lower()
                return f"{scheme}://{tokens[1]}"
        # Format đơn giản: host:port
        if ":" in clean and "@" not in clean:
            # Đếm số : để xác định có phải host:port không
            if clean.count(":") == 1:
                return f"http://{clean}"
        return f"http://{clean}"

    # Format có :// nhưng scheme không hợp lệ
    try:
        scheme, rest = clean.split("://", 1)
        scheme = scheme.lower()
        if scheme not in {"http", "https", base64.b64decode('c29ja3M0').decode(), (chr(115)+chr(111)+chr(99)+chr(107)+chr(115)+chr(53))}:
            return f"http://{rest}"
        return f"{scheme}://{rest}"
    except (ValueError, AttributeError):
        # Nếu không parse được, thử thêm http://
        return f"http://{clean}"


def _parse_custom_proxy_file(text: str):
    proxies = []
    for line in text.splitlines():
        entry = _normalize_proxy_entry(line)
        if entry:
            proxies.append(entry)
    return proxies


def _parse_geonode_payload(payload):
    proxies = []
    try:
        data = payload if isinstance(payload, dict) else json.loads(payload)
    except Exception:
        return proxies

    for entry in data.get("data", []):
        ip = entry.get("ip")
        port = entry.get("port")
        protocols = entry.get(bytes.fromhex('70726f746f636f6c73').decode()) or []
        if not ip or not port:
            continue
        if not any(proto in ("http", "https") for proto in protocols):
            continue
        proxies.append(f"http://{ip}:{port}")
    return proxies


PROXY_SOURCES = [
    {"name": "monosans-proxy-list", "url": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt", "parser": _parse_proxy_lines},
    {"name": "mmpx12-proxy-list", "url": "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt", base64.b64decode('cGFyc2Vy').decode(): _parse_proxy_lines},
    {"name": base64.b64decode('cm9vc3RlcmtpZC1wcm94eS1saXN0').decode(), "url": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt", "parser": _parse_proxy_lines},
    {"name": "proxyscrape-free-list", "url": "https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&skip=0&limit=2000", base64.b64decode('cGFyc2Vy').decode(): _parse_proxy_lines},
    {"name": bytes.fromhex('70726f7869666c792d687474702d6c697374').decode(), "url": "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt", "parser": _parse_proxy_lines},
    {"name": "hideip-http-list", "url": "https://github.com/zloi-user/hideip.me/raw/refs/heads/master/http.txt", (chr(112)+chr(97)+chr(114)+chr(115)+chr(101)+chr(114)): _parse_proxy_lines},
    # {"name": "thespeedx-proxy-list", "url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", "parser": _parse_proxy_lines},
    {"name": "sunoochi-proxy-list", "url": "https://raw.githubusercontent.com/sunoochi/Proxy-List/main/http.txt", base64.b64decode('cGFyc2Vy').decode(): _parse_proxy_lines},
    {"name": "userr3x-proxy-list", "url": "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/http.txt", bytes.fromhex('706172736572').decode(): _parse_proxy_lines},
    {"name": "clarketm-proxy-list", "url": "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt", base64.b64decode('cGFyc2Vy').decode(): _parse_proxy_lines},
    {"name": bytes.fromhex('61736c69736b2d70726f78792d6c697374').decode(), "url": "https://raw.githubusercontent.com/aslisk/proxyhttps/main/https.txt", "parser": _parse_proxy_lines},
    {"name": bytes.fromhex('7264617679646f762d70726f78792d6c697374').decode(), "url": "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt", base64.b64decode('cGFyc2Vy').decode(): _parse_proxy_lines},
    {"name": base64.b64decode('bWVydGd1dmVuY2xpLXByb3h5LWxpc3Q=').decode(), "url": "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt", (chr(112)+chr(97)+chr(114)+chr(115)+chr(101)+chr(114)): _parse_proxy_lines},
    {"name": base64.b64decode('cHJveHlsaXN0LWdlb25vZGUtYXBp').decode(), "url": "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps", (chr(112)+chr(97)+chr(114)+chr(115)+chr(101)+chr(114)): _parse_geonode_payload, "is_api": True},
    {"name": "speedx-socks5-list", "url": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt", (chr(112)+chr(97)+chr(114)+chr(115)+chr(101)+chr(114)): _build_scheme_parser("socks5")},
    {"name": "speedx-socks4-list", "url": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt", bytes.fromhex('706172736572').decode(): _build_scheme_parser(bytes.fromhex('736f636b7334').decode())},
    {"name": "speedx-http-list", "url": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt", "parser": _parse_proxy_lines},
]


class ProxyManager:
    CACHE_DURATION = 30 * 60  # 30 phút
    TEST_BATCH_SIZE = 1000
    MIN_WORKING_REQUIRED = 40
    # Tối ưu: Giới hạn threads dựa trên CPU cores để tránh quá tải
    TEST_THREADS = min(200, (os.cpu_count() or 1) * 20)  # Tối đa 200 threads
    BUFFER_TARGET = 80
    MAINTAIN_INTERVAL = 120
    REQUEST_RETRIES = 3
    TEST_TIMEOUT = 10
    # Giới hạn memory leak: cleanup khi vượt quá số lượng này
    MAX_USAGE_TRACKING = 2000
    # Multiple test URLs for better reliability
    TEST_URLS = [
        "http://httpbin.org/ip",
        "https://httpbin.org/ip",
        "http://icanhazip.com",
        "http://api.ipify.org?format=json",
        "https://www.google.com/generate_204",
    ]
    TEST_URL = TEST_URLS[0]  # Default for backward compatibility
    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        base64.b64decode('QWNjZXB0').decode(): "application/json, text/plain, */*",
        bytes.fromhex('4163636570742d4c616e6775616765').decode(): "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    # Proxy rotation settings
    ROTATION_ENABLED = True  # Enable automatic proxy rotation
    ROTATION_AFTER_REQUESTS = 1  # Rotate after N requests (1 = every request)

    def __init__(self):
        self._lock = threading.Lock()
        self._proxies = []
        self._last_refresh = 0
        self._refreshing = False
        self._in_use = set()
        self._free_sources_enabled = False
        self._proxy_disabled = False  # Flag để tắt scan proxy
        # Proxy rotation tracking: {proxy_url: request_count}
        self._proxy_usage_count = {}
        # Connection pooling: Session per proxy để tái sử dụng connections
        self._proxy_sessions = {}  # {proxy_url: requests.Session}
        self._maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self._maintenance_thread.start()

    def _log(self, message: str):
        # Log ra terminal và file
        log_msg = f"[ProxyManager] {message}"
        print(log_msg)
        _write_to_log_file(log_msg)

    def _cached_list(self):
        with self._lock:
            return list(self._proxies), self._last_refresh

    def _fetch_from_sources(self, limit=None, exclude=None, skip_sources=None):
        proxies = []
        exclude = set(exclude or [])
        skip_sources = set(skip_sources or [])
        seen = set()
        polled = set()
        used_sources = []
        target = limit if limit is not None and limit > 0 else None

        def _iter_sources(allow_skipped=False):
            if 0:
                _tmp = [i for i in range(1000)]
                del _tmp
            for source in PROXY_SOURCES:
                name = source["name"]
                if name in polled:
                    continue
                if not allow_skipped and name in skip_sources:
                    continue
                polled.add(name)
                yield source

        for allow_skipped in (False, True):
            for source in _iter_sources(allow_skipped):
                if target and len(proxies) >= target:
                    break
                name = source["name"]
                used_sources.append(name)
                try:
                    response = requests.get(
                        source["url"],
                        timeout=15,
                        headers=self.REQUEST_HEADERS
                    )
                    response.raise_for_status()
                    if source.get("is_api"):
                        parsed = source["parser"](response.json())
                    else:
                        parsed = source["parser"](response.text)
                    if not parsed:
                        continue

                    added = 0
                    for proxy in parsed:
                        if proxy in exclude or proxy in seen:
                            continue
                        proxies.append(proxy)
                        seen.add(proxy)
                        added += 1
                        if target and len(proxies) >= target:
                            break

                    if added:
                        self._log(f(chr(76)+chr(7845)+chr(121)+chr(32)+chr(273)+chr(432)+chr(7907)+chr(99)+chr(32)+chr(123)+chr(97)+chr(100)+chr(100)+chr(101)+chr(100)+chr(125)+chr(32)+chr(112)+chr(114)+chr(111)+chr(120)+chr(121)+chr(32)+chr(116)+chr(7915)+chr(32)+chr(123)+chr(110)+chr(97)+chr(109)+chr(101)+chr(125)))
                except Exception as exc:
                    self._log(f(chr(75)+chr(104)+chr(244)+chr(110)+chr(103)+chr(32)+chr(116)+chr(104)+chr(7875)+chr(32)+chr(108)+chr(7845)+chr(121)+chr(32)+chr(112)+chr(114)+chr(111)+chr(120)+chr(121)+chr(32)+chr(116)+chr(7915)+chr(32)+chr(123)+chr(110)+chr(97)+chr(109)+chr(101)+chr(125)+chr(58)+chr(32)+chr(123)+chr(101)+chr(120)+chr(99)+chr(125)))

            if target and len(proxies) >= target:
                break

        return proxies, used_sources

    def _test_proxy_once(self, proxy_url: str):
        """Test proxy with multiple URLs and protocol support - tối ưu với Session"""
        if not proxy_url:
            return None
        
        # Determine protocol from proxy URL
        proxy_lower = proxy_url.lower()
        is_socks5 = proxy_lower.startswith("socks5://")
        is_socks4 = proxy_lower.startswith("socks4://")
        
        # Build proxy dict for requests
        if is_socks5 or is_socks4:
            if not SOCKS_SUPPORT:
                return None  # SOCKS not supported
            proxies = {"http": proxy_url, "https": proxy_url}
        else:
            # HTTP/HTTPS proxy
            proxies = {"http": proxy_url, "https": proxy_url}
        
        # Sử dụng Session để tái sử dụng connection (nhanh hơn)
        session = requests.Session()
        session.proxies = proxies
        session.headers.update(self.REQUEST_HEADERS)
        
        try:
            # Try multiple test URLs for better reliability
            for test_url in self.TEST_URLS:
                try:
                    # For HTTPS URLs, disable SSL verification to avoid certificate issues
                    verify_ssl = not test_url.startswith('https://')
                    
                    start_time = time.time()
                    resp = session.get(
                        test_url,
                        timeout=self.TEST_TIMEOUT,
                        allow_redirects=True,
                        verify=verify_ssl,
                    )
                    response_time = time.time() - start_time
                    
                    # Consider 200-299 as success
                    if 200 <= resp.status_code < 300:
                        session.close()
                        return proxy_url
                        
                except requests.exceptions.SSLError:
                    # SSL error, try next URL
                    continue
                except requests.exceptions.Timeout:
                    # Timeout, try next URL
                    continue
                except requests.exceptions.ConnectionError:
                    # Connection error, try next URL
                    continue
                except requests.RequestException:
                    # Other request error, try next URL
                    continue
                except Exception:
                    # Unexpected error, try next URL
                    continue
        finally:
            session.close()
        
        return None

    def _test_batch(self, proxy_batch):
        working = []
        max_workers = min(self.TEST_THREADS, len(proxy_batch))
        with ThreadPoolExecutor(max_workers=max_workers or 1) as executor:
            futures = {executor.submit(self._test_proxy_once, proxy): proxy for proxy in proxy_batch}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    working.append(result)
        return working

    def _filter_working_proxies(self, proxy_list, required=None, allow_fetch_extra=True):
        if False:
            _ = lambda x: x + 1
            _ = sum(range(100))
        if not proxy_list:
            return []

        required = required or self.MIN_WORKING_REQUIRED
        working = []
        tested = 0
        start_idx = 0
        round_num = 1
        tested_proxies = set()
        known_proxies = set(proxy_list)
        session_sources_used = set()
        use_free_sources = self._free_sources_enabled

        while True:
            while start_idx < len(proxy_list):
                end_idx = min(start_idx + self.TEST_BATCH_SIZE, len(proxy_list))
                batch = [
                    proxy_list[idx]
                    for idx in range(start_idx, end_idx)
                    if proxy_list[idx] not in tested_proxies
                ]
                start_idx = end_idx
                if not batch:
                    continue

                tested += len(batch)
                tested_proxies.update(batch)

                self._log(f"Đang kiểm tra {len(batch)} proxy (đợt {round_num}) với {min(self.TEST_THREADS, len(batch))} luồng...")
                round_num += 1

                batch_working = self._test_batch(batch)
                for proxy in batch_working:
                    if proxy not in working:
                        working.append(proxy)

            if len(working) >= required or not allow_fetch_extra:
                break

            missing = max(required - len(working), 0)
            fetch_limit = max(missing * 3, min(self.TEST_BATCH_SIZE, 500)) or self.MIN_WORKING_REQUIRED
            fetched = []
            used_sources = []
            if use_free_sources:
                fetched, used_sources = self._fetch_from_sources(
                    limit=fetch_limit,
                    exclude=tested_proxies.union(known_proxies),
                    skip_sources=session_sources_used
                )
            extra = [
                p for p in fetched
                if p not in tested_proxies and p not in proxy_list
            ]
            for name in used_sources:
                session_sources_used.add(name)
            if len(session_sources_used) >= len(PROXY_SOURCES):
                session_sources_used.clear()
            if not extra:
                break
            proxy_list.extend(extra)
            known_proxies.update(extra)

        self._log(f"Có {len(working)} proxy hoạt động sau khi kiểm tra {tested} proxy.")
        return working

    def _refresh(self, force=False):
        # Không refresh nếu proxy bị tắt
        with self._lock:
            if self._proxy_disabled:
                return []
        
        cached, _ = self._cached_list()
        existing = list(cached)
        existing_set = set(existing)

        if existing and not force and len(existing) >= self.MIN_WORKING_REQUIRED:
            self._log("Cache hiện đủ proxy, bỏ qua refresh.")
            return existing

        missing = max(self.MIN_WORKING_REQUIRED - len(existing), 0)
        required_new = self.MIN_WORKING_REQUIRED if (force or not existing) else missing
        if required_new <= 0:
            return existing

        fetch_limit = max(required_new * 4, self.MIN_WORKING_REQUIRED)
        candidates, _ = self._fetch_from_sources(limit=fetch_limit, exclude=existing_set)
        if not candidates:
            self._log("Không lấy được proxy mới, sử dụng cache cũ.")
            return existing

        working = self._filter_working_proxies(candidates, required=required_new)
        if not working:
            self._log("Không lấy được proxy mới khả dụng, sử dụng cache cũ.")
            return existing

        with self._lock:
            combined = []
            for proxy in working + self._proxies:
                if proxy not in combined:
                    combined.append(proxy)
            self._proxies = combined
            self._in_use.intersection_update(set(combined))
            self._last_refresh = time.time()

        if len(combined) < self.MIN_WORKING_REQUIRED:
            self._log(f"Không đủ proxy hoạt động (tìm được {len(combined)}/{self.MIN_WORKING_REQUIRED}).")
        return list(combined)

    def ensure_cache(self, force=False):
        if not True:
            _dummy = {'a': 1, 'b': 2}
            _dummy.clear()
        cached, last_refresh = self._cached_list()
        expired = (time.time() - last_refresh) > self.CACHE_DURATION if last_refresh else True
        need_refresh = force or not cached or len(cached) < self.MIN_WORKING_REQUIRED or expired
        if need_refresh:
            return self._refresh(force=force or expired)
        return cached

    def acquire_proxy(self, exclude=None, enable_rotation=None):
        """
        Acquire a proxy. If rotation is enabled, prefer proxies with lower usage count.
        
        Args:
            exclude: Set of proxy URLs to exclude
            enable_rotation: Override global rotation setting (None = use global setting)
        """
        self.ensure_cache()
        rotation_enabled = enable_rotation if enable_rotation is not None else self.ROTATION_ENABLED
        
        with self._lock:
            use_free_sources = self._free_sources_enabled
            candidates = [
                proxy for proxy in self._proxies
                if proxy not in self._in_use and (not exclude or proxy not in exclude)
            ]
            if not candidates:
                if use_free_sources:
                    return None
                return None
            
            # If rotation is enabled, prefer proxies with lower usage count
            if rotation_enabled and self._proxy_usage_count:
                # Sort by usage count (ascending) and take from least used
                candidates_with_usage = [
                    (proxy, self._proxy_usage_count.get(proxy, 0))
                    for proxy in candidates
                ]
                candidates_with_usage.sort(key=lambda x: x[1])
                # Take from the least used proxies (top 30% or at least 1)
                top_count = max(1, len(candidates_with_usage) // 3)
                least_used = [p[0] for p in candidates_with_usage[:top_count]]
                proxy = random.choice(least_used)
            else:
                proxy = random.choice(candidates)
            
            self._in_use.add(proxy)
            # Track usage count for rotation
            self._proxy_usage_count[proxy] = self._proxy_usage_count.get(proxy, 0) + 1
            
            # Cleanup memory leak: xóa entries cũ nếu quá nhiều
            if len(self._proxy_usage_count) > self.MAX_USAGE_TRACKING:
                # Xóa 50% entries có usage count cao nhất (đã dùng nhiều)
                sorted_items = sorted(self._proxy_usage_count.items(), key=lambda x: x[1], reverse=True)
                to_remove = sorted_items[:self.MAX_USAGE_TRACKING // 2]
                for proxy_to_remove, _ in to_remove:
                    self._proxy_usage_count.pop(proxy_to_remove, None)
                    # Cleanup session nếu có
                    self._proxy_sessions.pop(proxy_to_remove, None)
            
            return proxy

    def release_proxy(self, proxy_url: str, force_rotation=False):
        """
        Release a proxy. If force_rotation is True or usage count exceeds threshold,
        the proxy will be released and usage count may be reset.
        
        Args:
            proxy_url: Proxy URL to release
            force_rotation: Force rotation by resetting usage count
        """
        if not proxy_url:
            return
        with self._lock:
            self._in_use.discard(proxy_url)
            # If rotation is enabled and usage count exceeds threshold, reset it
            if self.ROTATION_ENABLED and proxy_url in self._proxy_usage_count:
                usage_count = self._proxy_usage_count[proxy_url]
                if force_rotation or usage_count >= self.ROTATION_AFTER_REQUESTS:
                    # Reset usage count to allow this proxy to be used again
                    self._proxy_usage_count[proxy_url] = 0

    def get_proxy(self, exclude=None):
        return self.acquire_proxy(exclude)

    def report_failure(self, proxy_url: str, reason: str = ""):
        if not proxy_url:
            return
        removed = False
        need_refresh = False
        with self._lock:
            self._in_use.discard(proxy_url)
            if proxy_url in self._proxies:
                self._proxies.remove(proxy_url)
                removed = True
                threshold = max(self.MIN_WORKING_REQUIRED, self.BUFFER_TARGET // 2)
                need_refresh = len(self._proxies) < threshold
        if removed and DEBUG_MODE:
            self._log(f"Gỡ proxy lỗi {proxy_url} {reason}")
        if need_refresh:
            self.refresh_async(force=True)

    def as_requests_proxy(self, proxy_url: str):
        if not True:
            _dummy = {'a': 1, 'b': 2}
            _dummy.clear()
        if not proxy_url:
            return None
        return {"http": proxy_url, "https": proxy_url}
    
    def get_session(self, proxy_url: str):
        if not True:
            _dummy = {'a': 1, 'b': 2}
            _dummy.clear()
        """Lấy hoặc tạo Session với connection pooling cho proxy"""
        if not proxy_url:
            return None
        
        # Kiểm tra cache session
        if proxy_url in self._proxy_sessions:
            return self._proxy_sessions[proxy_url]
        
        # Tạo session mới với connection pooling
        session = requests.Session()
        session.proxies = self.as_requests_proxy(proxy_url)
        session.headers.update(self.REQUEST_HEADERS)
        # Connection pooling: tái sử dụng connections
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=2,  # Số connection pools
            pool_maxsize=10,     # Max connections per pool
            max_retries=0        # Không retry tự động (đã xử lý ở trên)
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        with self._lock:
            self._proxy_sessions[proxy_url] = session
        
        return session

    def has_minimum_ready(self):
        if 0:
            _tmp = [i for i in range(1000)]
            del _tmp
        with self._lock:
            return len(self._proxies) >= self.MIN_WORKING_REQUIRED

    def is_refreshing(self):
        if False:
            _ = lambda x: x + 1
            _ = sum(range(100))
        with self._lock:
            return self._refreshing

    def refresh_async(self, force=False):
        # Không refresh nếu proxy bị tắt
        with self._lock:
            if self._proxy_disabled:
                return
            if self._refreshing:
                return
            self._refreshing = True

        def _runner():
            try:
                self.ensure_cache(force=force)
            finally:
                with self._lock:
                    self._refreshing = False

        threading.Thread(target=_runner, daemon=True).start()

    def _maintenance_loop(self):
        while True:
            time.sleep(self.MAINTAIN_INTERVAL)
            # Không scan nếu proxy bị tắt
            with self._lock:
                if self._proxy_disabled:
                    continue
                needs_topup = len(self._proxies) < self.BUFFER_TARGET
            if needs_topup:
                self.refresh_async(force=True)

    def load_from_file(self, file_path: str):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)

        try:
            with open(file_path, "r", encoding="utf-8(chr(44)+chr(32)+chr(101)+chr(114)+chr(114)+chr(111)+chr(114)+chr(115)+chr(61))ignore") as fp:
                text = fp.read()
        except Exception as exc:
            raise IOError(fbytes.fromhex('4b68c3b46e6720c491e1bb8d6320c491c6b0e1bba3632066696c652070726f78793a207b6578637d').decode()) from exc

        proxies = _parse_custom_proxy_file(text)
        if not proxies:
            return 0

        working = self._filter_working_proxies(
            proxies,
            required=max(len(proxies), self.MIN_WORKING_REQUIRED),
            allow_fetch_extra=False,
        )
        if not working:
            return 0

        with self._lock:
            combined = []
            for proxy in working + self._proxies:
                if proxy not in combined:
                    combined.append(proxy)
            self._proxies = combined
            self._in_use.intersection_update(set(combined))
            self._last_refresh = time.time()
        return len(working)

    def set_free_sources_enabled(self, enabled: bool):
        with self._lock:
            if self._free_sources_enabled == enabled:
                return
            self._free_sources_enabled = enabled
        if enabled:
            self.refresh_async(force=True)

    def free_sources_enabled(self):
        with self._lock:
            return self._free_sources_enabled

    def set_proxy_disabled(self, disabled: bool):
        """Tắt/bật proxy - khi tắt sẽ không scan proxy nữa"""
        with self._lock:
            if self._proxy_disabled == disabled:
                return
            self._proxy_disabled = disabled
        if disabled:
            self._log("Đã tắt scan proxy - không còn refresh proxy nữa.")
        else:
            self._log("Đã bật scan proxy - sẽ tiếp tục refresh proxy.")
    
    def set_rotation_enabled(self, enabled: bool):
        """Enable or disable proxy rotation"""
        with self._lock:
            self.ROTATION_ENABLED = enabled
            if not enabled:
                # Reset all usage counts when disabling rotation
                self._proxy_usage_count.clear()
    
    def set_rotation_after_requests(self, count: int):
        """Set number of requests after which to rotate proxy"""
        with self._lock:
            self.ROTATION_AFTER_REQUESTS = max(1, count)
    
    def reset_proxy_usage(self, proxy_url: str = None):
        """Reset usage count for a specific proxy or all proxies"""
        with self._lock:
            if proxy_url:
                self._proxy_usage_count.pop(proxy_url, None)
            else:
                self._proxy_usage_count.clear()
    
    def get_proxy_stats(self):
        if False:
            _ = lambda x: x + 1
            _ = sum(range(100))
        """Get statistics about proxy usage"""
        with self._lock:
            total_proxies = len(self._proxies)
            in_use = len(self._in_use)
            available = total_proxies - in_use
            avg_usage = sum(self._proxy_usage_count.values()) / len(self._proxy_usage_count) if self._proxy_usage_count else 0
            return {
                "total": total_proxies,
                "in_use": in_use,
                "available": available,
                "average_usage": avg_usage,
                "rotation_enabled": self.ROTATION_ENABLED,
                "rotation_threshold": self.ROTATION_AFTER_REQUESTS
            }


proxy_manager = ProxyManager()
proxy_manager.refresh_async(force=True)


# ======================================
# SIGNALS
# ======================================
class WorkerSignals(QObject):
    status = pyqtSignal(str, str, str)   # prompt, status, reason/url
    finished = pyqtSignal(str, dict)     # prompt, result
    log = pyqtSignal(str)                # line log
    token_expired = pyqtSignal()


class ProxyLoaderThread(QThread):
    finished = pyqtSignal(str, int, str)  # path, count, error

    def __init__(self, path: str):
        super().__init__()
        self.path = path

    def run(self):
        try:
            count = proxy_manager.load_from_file(self.path)
            self.finished.emit(self.path, count, None)
        except Exception as exc:
            self.finished.emit(self.path, 0, str(exc))


# ======================================
# WORKER
# ======================================
class VideoTaskWorker(QRunnable):
    """
    Worker chuẩn API: log terminal + panel, fallback portrait, poll đến khi xong.
    """
    MAX_ATTEMPTS = 3
    RETRY_DELAY = 5
    REQUEST_TIMEOUT = 10
    # Rate limiting cho direct request (không dùng proxy)
    DIRECT_REQUEST_DELAY = 1.0  # Delay giữa các request (tăng từ 0.5s lên 1s)
    DIRECT_429_BACKOFF_BASE = 2  # Exponential backoff base cho 429
    DIRECT_429_MAX_DELAY = 60  # Max delay cho 429 (giây)
    DIRECT_429_RETRIES = 5  # Số lần retry cho 429
    DIRECT_REQUEST_TIMEOUT = 20  # Timeout cho direct request (tăng từ 10s lên 20s)

    def __init__(self, access_token, prompt, stop_flag, aspect_ratio="VIDEO_ASPECT_RATIO_LANDSCAPE", disable_proxy=False):
        super().__init__()
        self.access_token = access_token
        self.prompt = prompt
        self.signals = WorkerSignals()
        self.stop_flag = stop_flag
        self.aspect_ratio = aspect_ratio
        self.scene_id = str(uuid.uuid4())
        self.disable_proxy = disable_proxy

    # ---------- utils ----------
    def _log(self, msg: str):
        if 0:
            _tmp = [i for i in range(1000)]
            del _tmp
        print(msg)
        _write_to_log_file(msg)
        self.signals.log.emit(msg)

    def _request_direct_with_rate_limit(self, method, url, timeout=None, **kwargs):
        """
        Thuật toán riêng cho request không dùng proxy:
        - Rate limiting: delay giữa các request với jitter
        - Exponential backoff với jitter cho 429 (tránh thundering herd)
        - Retry logic thông minh
        - Timeout tăng cho check status
        """
        # Timeout tăng cho check status requests
        if "batchCheckAsyncVideoGenerationStatus" in url:
            timeout = timeout or self.DIRECT_REQUEST_TIMEOUT
        else:
            timeout = timeout or self.REQUEST_TIMEOUT
        
        request_kwargs = dict(kwargs)
        
        # Rate limiting: delay trước mỗi request với jitter (random 0-0.5s)
        base_delay = self.DIRECT_REQUEST_DELAY
        jitter = random.uniform(0, 0.5)
        time.sleep(base_delay + jitter)
        
        last_error = None
        retry_count = 0
        
        while retry_count <= self.DIRECT_429_RETRIES:
            try:
                self._log(f"[REQUEST] {method} {url} (direct, retry {retry_count})")
                response = requests.request(method, url, timeout=timeout, **request_kwargs)
                status_code = response.status_code
                self._log(f"[RESPONSE] {method} {url} - Status: {status_code}")
                
                # Xử lý 429 với exponential backoff + jitter
                if status_code == 429:
                    if retry_count < self.DIRECT_429_RETRIES:
                        # Exponential backoff: 2^retry_count giây, max 60s
                        base_backoff = min(
                            self.DIRECT_429_BACKOFF_BASE ** retry_count,
                            self.DIRECT_429_MAX_DELAY
                        )
                        # Thêm jitter ±20% để tránh thundering herd
                        jitter_factor = random.uniform(0.8, 1.2)
                        backoff_delay = base_backoff * jitter_factor
                        self._log(f"[RATE_LIMIT] HTTP 429 - Đợi {backoff_delay:.1f}s trước khi retry...")
                        time.sleep(backoff_delay)
                        retry_count += 1
                        continue
                    else:
                        # Đã retry hết, raise error
                        response.raise_for_status()
                
                # Success hoặc lỗi khác (không phải 429)
                response.raise_for_status()
                return response
                
            except requests.HTTPError as http_err:
                status_code = getattr(http_err.response, "status_code", None)
                if status_code == 429:
                    last_error = http_err
                    if retry_count < self.DIRECT_429_RETRIES:
                        base_backoff = min(
                            self.DIRECT_429_BACKOFF_BASE ** retry_count,
                            self.DIRECT_429_MAX_DELAY
                        )
                        jitter_factor = random.uniform(0.8, 1.2)
                        backoff_delay = base_backoff * jitter_factor
                        self._log(f"[RATE_LIMIT] HTTP 429 - Đợi {backoff_delay:.1f}s trước khi retry...")
                        time.sleep(backoff_delay)
                        retry_count += 1
                        continue
                # Lỗi HTTP khác (không phải 429)
                self._log(f"[ERROR] HTTP {status_code} - {http_err}")
                raise http_err
                
            except requests.RequestException as exc:
                # Network errors - retry với exponential backoff nhỏ
                if retry_count < 2:  # Chỉ retry 2 lần cho network errors
                    retry_delay = (retry_count + 1) * 1.5  # 1.5s, 3s
                    self._log(f"[NETWORK_ERROR] {exc} - Retry sau {retry_delay:.1f}s...")
                    time.sleep(retry_delay)
                    retry_count += 1
                    continue
                self._log(f"[ERROR] RequestException - {exc}")
                raise exc
                
            except Exception as exc:
                self._log(f"[ERROR] Exception - {exc}")
                raise exc
        
        # Đã retry hết cho 429
        if last_error:
            self._log(f"[ERROR] Đã retry {self.DIRECT_429_RETRIES} lần cho 429, dừng lại.")
            raise last_error
        
        raise requests.RequestException(f"Không thể gửi request sau {retry_count} lần thử.")

    def _request_with_proxy(self, method, url, **kwargs):
        timeout = kwargs.pop("timeout", self.REQUEST_TIMEOUT)
        request_kwargs = dict(kwargs)
        
        # Nếu tắt proxy, dùng thuật toán riêng cho direct request
        if self.disable_proxy:
            return self._request_direct_with_rate_limit(method, url, timeout=timeout, **request_kwargs)
        
        # Sử dụng proxy như bình thường
        last_error = None
        attempted = set()
        refresh_attempted = False
        rotation_enabled = proxy_manager.ROTATION_ENABLED
        
        self._log(f"[REQUEST] {method} {url} (dùng proxy)")
        
        # Thuật toán cũ: mỗi request lấy proxy mới, không giữ proxy pool
        for _ in range(ProxyManager.REQUEST_RETRIES):
            # Acquire proxy với rotation support
            proxy_url = proxy_manager.acquire_proxy(exclude=attempted, enable_rotation=rotation_enabled)
            if not proxy_url:
                if refresh_attempted:
                    break
                proxy_manager.refresh_async(force=True)
                refresh_attempted = True
                time.sleep(1)
                continue
            attempted.add(proxy_url)
            self._log(f"[PROXY] Sử dụng proxy: {proxy_url[:50]}...")
            # Tối ưu: Sử dụng Session với connection pooling thay vì requests.request
            session = proxy_manager.get_session(proxy_url)
            try:
                response = session.request(method, url, timeout=timeout, **request_kwargs)
                self._log(f"[RESPONSE] {method} {url} - Status: {response.status_code} (proxy: {proxy_url[:30]}...)")
                if response.status_code == 429:
                    proxy_manager.report_failure(proxy_url, f"HTTP 429 {response.reason}")
                    last_error = requests.HTTPError(f"HTTP 429 {response.reason}", response=response)
                    # Release with force rotation on 429
                    proxy_manager.release_proxy(proxy_url, force_rotation=True)
                    continue
                # Success - release proxy với rotation nếu enabled
                proxy_manager.release_proxy(proxy_url, force_rotation=rotation_enabled)
                return response
            except requests.HTTPError as http_err:
                last_error = http_err
                status = getattr(http_err.response, "status_code", None)
                self._log(f"[ERROR] HTTP {status} - {http_err} (proxy: {proxy_url[:30]}...)")
                if status == 429:
                    proxy_manager.report_failure(proxy_url, "HTTP 429 Too Many Requests")
                    proxy_manager.release_proxy(proxy_url, force_rotation=True)
                    continue
                proxy_manager.report_failure(proxy_url, str(http_err))
                proxy_manager.release_proxy(proxy_url)
            except requests.RequestException as exc:
                last_error = exc
                self._log(f"[ERROR] RequestException - {exc} (proxy: {proxy_url[:30]}...)")
                proxy_manager.report_failure(proxy_url, str(exc))
                proxy_manager.release_proxy(proxy_url)
            except Exception as exc:
                # Unexpected error - release proxy
                last_error = exc
                self._log(f"[ERROR] Exception - {exc} (proxy: {proxy_url[:30]}...)")
                proxy_manager.release_proxy(proxy_url)
        if last_error:
            raise last_error
        raise requests.RequestException("Không còn proxy khả dụng.")

    # ---------- thread entry ----------
    def run(self):
        if self.stop_flag.is_set():
            self.signals.finished.emit(self.prompt, {"status": "STOPPED"})
            return

        attempt = 1
        last_error = None

        while attempt <= self.MAX_ATTEMPTS and not self.stop_flag.is_set():
            self.scene_id = str(uuid.uuid4())
            seed = random.randint(1000, 99999)
            attempt_label = f"lần {attempt}/{self.MAX_ATTEMPTS}"
            self._log(f"🚀 Bắt đầu xử lý prompt: {self.prompt} ({attempt_label})")
            self.signals.status.emit(self.prompt, f"Đang xử lý... ({attempt_label})", None)

            op_name, err_reason = self.start_video_generation(seed)
            if not op_name:
                last_error = err_reason
                if attempt < self.MAX_ATTEMPTS:
                    self._log(f"⚠️ Lỗi khởi tạo ({err_reason}). Thử lại sau {self.RETRY_DELAY}s.")
                    self._wait_before_retry()
                    attempt += 1
                    continue
                stop_requested = (err_reason or "").startswith("Access Token")
                self.signals.finished.emit(
                    self.prompt, {"status": "FAILED", "reason": err_reason})
                if stop_requested:
                    self.stop_flag.set()
                return

            # Poll trạng thái với exponential backoff (tối ưu thời gian chờ)
            poll_failed_reason = None
            poll_interval = 3  # Bắt đầu với 3 giây
            max_interval = 30  # Tối đa 30 giây
            min_interval = 3   # Tối thiểu 3 giây
            consecutive_pending = 0
            
            while not self.stop_flag.is_set():
                status, result = self.check_video_status(op_name)
                if status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                    self._log(f"🎬 Hoàn tất video cho: {self.prompt}")
                    self.signals.finished.emit(
                        self.prompt, {"status": "SUCCESSFUL", "url": result})
                    return
                elif status == "MEDIA_GENERATION_STATUS_FAILED":
                    poll_failed_reason = result
                    self._log(f"❌ Thất bại video cho: {self.prompt} ({result})")
                    break
                else:
                    if DEBUG_MODE:
                        self._log(f"[DEBUG] Status: {status} (chờ {poll_interval}s)")
                    self.signals.status.emit(
                        self.prompt, f"Đang xử lý... ({status})", None)
                    
                    # Exponential backoff: tăng dần thời gian chờ
                    consecutive_pending += 1
                    if consecutive_pending > 3:  # Sau 3 lần pending, tăng interval
                        poll_interval = min(poll_interval * 1.3, max_interval)
                    elif consecutive_pending == 1:
                        poll_interval = min_interval  # Reset về min khi có thay đổi
                    
                    time.sleep(poll_interval)

            if self.stop_flag.is_set():
                self.signals.finished.emit(self.prompt, {"status": "STOPPED"})
                return

            last_error = poll_failed_reason or "Không rõ nguyên nhân."
            if attempt < self.MAX_ATTEMPTS:
                self._log(f"🔁 Chuẩn bị thử lại sau {self.RETRY_DELAY}s (lỗi: {last_error}).")
                self._wait_before_retry()
                attempt += 1
                continue

            stop_requested = (last_error or "").startswith("Access Token")
            self.signals.finished.emit(
                self.prompt, {"status": "FAILED", "reason": last_error})
            if stop_requested:
                self.stop_flag.set()
            return

    def _wait_before_retry(self):
        if not True:
            _dummy = {'a': 1, 'b': 2}
            _dummy.clear()
        for _ in range(self.RETRY_DELAY):
            if self.stop_flag.is_set():
                break
            time.sleep(1)

    # ---------- API calls ----------

    def start_video_generation(self, seed):
        if 0:
            _tmp = [i for i in range(1000)]
            del _tmp
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        aspect_ratio = self.aspect_ratio
        video_model_key = model_key_for(aspect_ratio)

        json_data = {
            "clientContext": {
                "sessionId": f"user-{int(time.time() * 1000)}",
                "projectId": "b62e5baf-4aae-4d15-8d73-6102f13f57f3",
                "tool": "PINHOLE",
                "userPaygateTier": "PAYGATE_TIER_TWO"
            },
            "requests": [{
                "aspectRatio": aspect_ratio,
                "seed": seed,
                "textInput": {"prompt": self.prompt},
                "metadata": {"sceneId": self.scene_id},
                "videoModelKey": video_model_key
            }]
        }

        try:
            # Gửi request chính
            response = self._request_with_proxy(
                "POST",
                START_GENERATION_URL,
                headers=headers,
                json=json_data,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            op_name = data.get("operations", [{}])[0].get(
                "operation", {}).get("name")
            self._log("✅ Yêu cầu tạo video đã được gửi thành công.")
            return op_name, None

        except requests.exceptions.HTTPError as http_err:
            # Lấy mã lỗi HTTP
            try:
                status_code = http_err.response.status_code
                msg = http_err.response.json().get("error", {}).get("message", "")
            except Exception:
                status_code = None
                msg = str(http_err)
            self._log(f"[HTTP ERROR] status={status_code} detail={msg}")

            # ⚠️ Token hết hạn / không hợp lệ
            if status_code == 401:
                self._log("⚠️ Access Token đã hết hạn hoặc không hợp lệ.")
                try:
                    self.signals.token_expired.emit()

                except Exception:
                    pass
                return None, "Access Token không hợp lệ hoặc đã hết hạn."

            # ⚙️ Fallback nếu không hỗ trợ landscape
            if "INVALID_ARGUMENT" in msg or "invalid" in msg.lower():
                self._log(
                    "⚙️ Server không hỗ trợ tỉ lệ này — chuyển sang chế độ dọc (portrait).")
                self.aspect_ratio = "VIDEO_ASPECT_RATIO_PORTRAIT"
                json_data["requests"][0]["aspectRatio"] = self.aspect_ratio
                json_data["requests"][0]["videoModelKey"] = model_key_for(
                    self.aspect_ratio)

                try:
                    response = self._request_with_proxy(
                        "POST",
                        START_GENERATION_URL,
                        headers=headers,
                        json=json_data,
                        timeout=self.REQUEST_TIMEOUT
                    )
                    response.raise_for_status()
                    data = response.json()
                    op_name = data.get("operations", [{}])[0].get(
                        "operation", {}).get("name")
                    self._log("✅ Fallback sang portrait thành công.")
                    return op_name, None
                except Exception:
                    self._log("❌ Fallback thất bại.")
                    return None, "Lỗi khi fallback sang portrait."

            # 🟥 Các lỗi khác
            self._log(f"❌ Đã xảy ra lỗi trong quá trình gửi yêu cầu (HTTP {status_code}).")
            return None, f"Lỗi trong quá trình gửi yêu cầu (HTTP {status_code})."

        except Exception as exc:
            self._log(f"❌ Đã xảy ra lỗi không xác định khi tạo video: {exc}")
            return None, f"Lỗi không xác định: {exc}"

    def check_video_status(self, op_name):
        if 0:
            _tmp = [i for i in range(1000)]
            del _tmp
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        json_data = {"operations": [
            {"operation": {"name": op_name}, "sceneId": self.scene_id}]}
        try:
            response = self._request_with_proxy(
                "POST",
                CHECK_STATUS_URL,
                headers=headers,
                json=json_data,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            if DEBUG_MODE:
                self._log(
                    f"[DEBUG] Response:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            ops = data.get("operations", [])
            if not ops:
                # Không có dữ liệu nhưng vẫn tiếp tục poll với cùng proxy
                return "MEDIA_GENERATION_STATUS_PENDING", None
            op = ops[0]
            status = op.get("status", "MEDIA_GENERATION_STATUS_FAILED")
            if status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                url = op.get("operation", {}).get(
                    "metadata", {}).get("video", {}).get("fifeUrl")
                return status, url
            elif status == "MEDIA_GENERATION_STATUS_FAILED":
                reason = op.get("error", {}).get("message", "Lỗi không rõ.")
                return status, reason
            return status, None
        except requests.HTTPError as http_err:
            # Kiểm tra nếu là 429 thì đổi proxy, còn lại vẫn giữ proxy để poll tiếp
            status_code = getattr(http_err.response, "status_code", None)
            if status_code == 429:
                self._log(f"[LỖI CHECK STATUS - 429] {http_err}")
                # 429 sẽ được xử lý trong _request_with_proxy để đổi proxy
                # Trả về pending để tiếp tục poll với proxy mới
                return "MEDIA_GENERATION_STATUS_PENDING", None
            else:
                # Lỗi khác: vẫn giữ proxy, tiếp tục poll
                if DEBUG_MODE:
                    self._log(f"[LỖI CHECK STATUS - HTTP {status_code}] {http_err}")
                return "MEDIA_GENERATION_STATUS_PENDING", None
        except Exception as e:
            # Lỗi khác: vẫn giữ proxy, tiếp tục poll
            if DEBUG_MODE:
                self._log(f"[LỖI CHECK STATUS] {e}")
            return "MEDIA_GENERATION_STATUS_PENDING", None


class CustomCheckBox(QCheckBox):
    """Checkbox với màu sắc dịu mắt hơn"""

    def paintEvent(self, event):
        if 0:
            _tmp = [i for i in range(1000)]
            del _tmp
        size = 18
        margin = (self.height() - size) / 2
        rect = QRectF(2, margin, size, size)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.isChecked():
            # Background xám khi checked
            painter.setBrush(QColor("#555555"))
            pen = QPen(QColor("#777777"))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRoundedRect(rect, 4, 4)
            
            # Dấu check mark
            pen = QPen(QColor("#ffffff"))
            pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            # Vẽ dấu check
            check_points = [
                (rect.left() + 4, rect.center().y()),
                (rect.center().x() - 1, rect.bottom() - 4),
                (rect.right() - 4, rect.top() + 4)
            ]
            painter.drawLine(int(check_points[0][0]), int(check_points[0][1]),
                          int(check_points[1][0]), int(check_points[1][1]))
            painter.drawLine(int(check_points[1][0]), int(check_points[1][1]),
                          int(check_points[2][0]), int(check_points[2][1]))
        else:
            # Viền khi unchecked - xám
            pen = QPen(QColor(base64.b64decode('IzMzMzMzMw==').decode()))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, 4, 4)


class PlainTextEdit(QTextEdit):
    """Tự động loại bỏ định dạng khi dán văn bản (fix chữ đen trên nền đen)."""

    def insertFromMimeData(self, source):
        if source.hasText():
            self.insertPlainText(source.text())  # chỉ dán text thường
        else:
            super().insertFromMimeData(source)


class MainWindow(QMainWindow):
    def __init__(self):
        if 0:
            _tmp = [i for i in range(1000)]
            del _tmp
        super().__init__()
        self.token_warning_shown = False

        self.setWindowTitle(APP_TITLE)
        # Kích thước ban đầu với tỉ lệ tốt, giữ nguyên tỉ lệ khi phóng to
        self.setGeometry(80, 60, 1200, 700)

        self.settings = QSettings("Kuro", "VeoTool")
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(12)  # Max 12 luồng cùng lúc
        self.proxy_loader_thread = None
        self.stop_flag = threading.Event()
        self.worker_launch_queue = []
        self.launch_timer = QTimer(self)
        self.launch_timer.setSingleShot(True)
        self.launch_timer.timeout.connect(self._launch_next_prompt)
        self.job_table_map = {}        # prompt -> row
        self.simulating_jobs = set()
        self.failed_prompts = set()
        self.is_running = False
        self.pending_prompts = []
        self.generation_initialized = False
        # Lưu danh sách prompts ban đầu để lấy prompt tiếp theo sau mỗi video
        self.all_prompts = []  # Danh sách tất cả prompts
        self.current_prompt_index = 0  # Index của prompt hiện tại
        # Thời gian tracking
        self.start_time = None
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self._update_elapsed_time)
        self.elapsed_timer.setInterval(1000)  # Cập nhật mỗi giây

        self.progress_simulator_timer = QTimer(self)
        self.progress_simulator_timer.timeout.connect(self.simulate_progress)
        self.proxy_ready_timer = QTimer(self)
        self.proxy_ready_timer.setInterval(2000)
        self.proxy_ready_timer.timeout.connect(self._try_start_pending_prompts)

        self._build_ui()
        self._load_settings()

    # ---------- UI ----------
    def _build_ui(self):
        main = QWidget()
        root_parent = QVBoxLayout(main)            # layout root
        root_parent.setContentsMargins(12, 12, 12, 12)
        root_parent.setSpacing(12)

        # Layout ngang chia 2 phần
        root = QHBoxLayout()
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(16)

        # LEFT: Nhập prompt
        left_container = QWidget()
        left = QVBoxLayout(left_container)
        left.setSpacing(12)
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Tabs giả (cho giống ảnh)
        tabs_bar = QHBoxLayout()
        tabs_bar.setSpacing(6)
        for t in ["Text to Video", "Image to Video", "Start-End", "Đồng bộ nhân vật"]:
            b = QPushButton(t)
            b.setEnabled(t == "Text to Video")  # fake
            b.setStyleSheet("padding: 6px 12px; font-size: 9.5pt;")
            tabs_bar.addWidget(b)
        tabs_bar.addStretch(1)
        left.addLayout(tabs_bar)

        # Prompt box
        prompt_group = QGroupBox("Danh sách prompt")
        prompt_v = QVBoxLayout(prompt_group)
        self.prompt_input = PlainTextEdit()
        self.prompt_input.setPlaceholderText("Mỗi dòng là một prompt…")
        prompt_v.addWidget(self.prompt_input)
        left.addWidget(prompt_group, 1)

        # Duration (fake)
        duration_row = QHBoxLayout()
        # duration_row.addWidget(QLabel("Thời lượng mỗi video"))
        # down = QPushButton("▾")
        # down.setEnabled(False)
        # duration_row.addStretch(1)
        # self.duration_label = QLabel("8 giây")
        # duration_row.addWidget(down)
        # duration_row.addWidget(self.duration_label)
        left.addLayout(duration_row)

        # Bottom controls
        bottom_controls = QHBoxLayout()
        self.start_btn = QPushButton("🚀 BẮT ĐẦU TẠO VIDEO")
        self.start_btn.clicked.connect(self.toggle_generation)
        self.cancel_btn = QPushButton("⏹️ Dừng lại")
        self.cancel_btn.clicked.connect(self.toggle_generation)
        self.cancel_btn.setVisible(False)
        bottom_controls.addWidget(self.start_btn)
        bottom_controls.addWidget(self.cancel_btn)

        # 1080p (fake)
        self.hd_btn = QPushButton("1080p")
        self.hd_btn.setEnabled(False)
        bottom_controls.addWidget(self.hd_btn)
        left.addLayout(bottom_controls)

        # Aspect + Save dir
        config_row_1 = QHBoxLayout()
        left.addLayout(config_row_1)

        aspect_group = QGroupBox("Tỷ lệ khung hình")
        aspect_l = QVBoxLayout(aspect_group)
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(["16:9 (Ngang)", "9:16 (Dọc)"])
        # mặc định Ngang (UI), API vẫn fallback portrait
        self.aspect_combo.setCurrentIndex(0)
        aspect_l.addWidget(self.aspect_combo)

        path_group = QGroupBox("Chọn thư mục lưu video")
        path_l = QHBoxLayout(path_group)
        path_l.setSpacing(8)
        self.save_path_input = QLineEdit()
        browse = QPushButton("📂 Duyệt")
        browse.setFixedWidth(90)
        browse.clicked.connect(self.browse_save_path)
        path_l.addWidget(self.save_path_input)
        path_l.addWidget(browse)

        config_row_1.addWidget(aspect_group, 1)
        config_row_1.addWidget(path_group, 2)

        # Token
        token_group = QGroupBox("Access Token")
        token_l = QVBoxLayout(token_group)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        token_l.addWidget(self.token_input)
        left.addWidget(token_group)

        # Custom proxy loader
        proxy_group = QGroupBox("Proxy thủ công (.txt)")
        proxy_l = QVBoxLayout(proxy_group)
        proxy_l.setSpacing(6)
        proxy_row = QHBoxLayout()
        self.proxy_file_input = QLineEdit()
        self.proxy_file_input.setPlaceholderText("Chọn file .txt chứa danh sách proxy")
        proxy_browse = QPushButton("📂 Chọn file")
        proxy_browse.setFixedWidth(110)
        proxy_browse.clicked.connect(self.browse_proxy_file)
        proxy_row.addWidget(self.proxy_file_input)
        proxy_row.addWidget(proxy_browse)
        proxy_l.addLayout(proxy_row)

        proxy_action_row = QHBoxLayout()
        self.proxy_load_btn = QPushButton("Nạp proxy")
        self.proxy_load_btn.clicked.connect(self.load_proxy_file)
        self.proxy_file_status = QLabel("Chưa nhập proxy.")
        self.proxy_file_status.setStyleSheet("color: #9ca3af; font-size: 9pt;")
        proxy_action_row.addWidget(self.proxy_load_btn)
        proxy_action_row.addWidget(self.proxy_file_status, 1)
        proxy_l.addLayout(proxy_action_row)
        left.addWidget(proxy_group)

        # Free proxy toggle
        free_proxy_row = QHBoxLayout()
        free_proxy_row.setSpacing(8)
        self.free_proxy_btn = QPushButton()
        self.free_proxy_btn.setCheckable(True)
        self.free_proxy_btn.setFixedWidth(220)
        self.free_proxy_btn.setChecked(proxy_manager.free_sources_enabled())
        self.free_proxy_btn.toggled.connect(self.on_free_proxy_toggled)
        free_proxy_row.addWidget(self.free_proxy_btn)
        self._update_free_proxy_btn_text(proxy_manager.free_sources_enabled())
        free_hint = QLabel("Proxy free Ko ổn định")
        free_hint.setStyleSheet("color: #9ca3af; font-size: 9pt;")
        free_proxy_row.addWidget(free_hint, 1)
        left.addLayout(free_proxy_row)

        # Disable proxy toggle - dùng button giống free proxy để nhất quán
        disable_proxy_row = QHBoxLayout()
        disable_proxy_row.setSpacing(8)
        self.disable_proxy_btn = QPushButton()
        self.disable_proxy_btn.setCheckable(True)
        self.disable_proxy_btn.setFixedWidth(220)
        self.disable_proxy_btn.setChecked(False)
        self.disable_proxy_btn.toggled.connect(self.on_disable_proxy_toggled)
        disable_proxy_row.addWidget(self.disable_proxy_btn)
        self._update_disable_proxy_btn_text(False)
        disable_hint = QLabel("Gửi request trực tiếp, không qua proxy")
        disable_hint.setStyleSheet("color: #9ca3af; font-size: 9pt;")
        disable_proxy_row.addWidget(disable_hint, 1)
        left.addLayout(disable_proxy_row)

        # Log panel nhỏ
        log_group = QGroupBox("Logs")
        log_v = QVBoxLayout(log_group)
        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.setFixedHeight(120)
        log_v.addWidget(self.log_panel)
        # Bỏ các nút thừa ở đây
        left.addWidget(log_group, 0)

        # RIGHT: Kết quả video
        right_container = QWidget()
        right = QVBoxLayout(right_container)
        right.setSpacing(12)
        right_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Toolbar - Nhỏ lại và nằm trên đầu, đồng nhất kích thước
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)
        for name in ["Tạo lại video", "Tạo lại video lỗi", "Cắt ảnh cuối", "Xóa kết quả", "Nhóm zalo"]:
            b = QPushButton(name)
            b.setStyleSheet("padding: 4px 8px; font-size: 8.5pt; min-height: 24px; min-width: 85px;")
            if name == "Tạo lại video lỗi":
                self.retry_failed_btn = b
                b.clicked.connect(self.retry_failed_prompts)
                b.setEnabled(False)
            elif name == "Xóa kết quả":
                self.clear_results_btn = b
                b.clicked.connect(self.clear_results)
            else:
                b.setEnabled(False)  # fake
            toolbar.addWidget(b)
        
        # Nút tải video (từng file riêng)
        self.download_selected_btn = QPushButton("⬇️ Tải video")
        self.download_selected_btn.setToolTip("Tải từng video đã chọn (không ghép).")
        self.download_selected_btn.setStyleSheet("padding: 4px 8px; font-size: 8.5pt; min-height: 24px; min-width: 85px;")
        self.download_selected_btn.clicked.connect(self.download_selected_videos)
        self.download_selected_btn.setEnabled(False)
        toolbar.addWidget(self.download_selected_btn)
        
        # Nút tải và ghép video
        self.download_and_merge_btn = QPushButton("⬇️🔗 Tải và ghép video")
        self.download_and_merge_btn.setToolTip("Tải và ghép tất cả video đã chọn thành 1 file.")
        self.download_and_merge_btn.setStyleSheet("padding: 4px 8px; font-size: 8.5pt; min-height: 24px; min-width: 85px;")
        self.download_and_merge_btn.clicked.connect(self.download_and_merge_videos)
        self.download_and_merge_btn.setEnabled(False)
        toolbar.addWidget(self.download_and_merge_btn)
        
        toolbar.addStretch(1)
        right.addLayout(toolbar)

        # Table - Bảng tiến trình video (hiển thị ở bên phải)
        self.table = QTableWidget(0, 7)
        self.table.setStyleSheet("""
QTableWidget::item:selected {
    background-color: rgba(100, 100, 100, 0.2);
}
QTableWidget::item:hover {
    background-color: rgba(100, 100, 100, 0.12);
}
QTableView::item:focus {
    outline: none;
    background-color: rgba(100, 100, 100, 0.15);
}
QTableWidget::item {
    padding: 10px 4px;
}
""")
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setHorizontalHeaderLabels(
            ["", "STT", "Trạng thái", "Xem", "Prompt", "Tiến độ", "Hoàn thành"])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 40)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 100)  # Cột Trạng thái nhỏ lại
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 70)  # Cột Xem rộng hơn để chứa icon + text
        h.setStretchLastSection(True)
        self.table.setColumnWidth(6, 110)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Tăng chiều cao dòng để dễ chỉnh nút Xem và hiển thị rõ hơn
        self.table.verticalHeader().setDefaultSectionSize(55)
        right.addWidget(self.table, 1)

        # Account (fake)
        acct = QGroupBox("Thông tin")
        acct_l = QFormLayout(acct)
        acct_l.setSpacing(8)
        self.email_label = QLabel("Kuro - vibecoder")
        self.type_label = QLabel("Gói free")
        self.expiry_label = QLabel("vĩnh viễn")
        # self.usage_label = QLabel("0")
        self.limit_bar = QProgressBar()
        self.limit_bar.setValue(100)
        self.limit_bar.setTextVisible(True)
        # self.limit_bar.setFormat("Còn 999 tỷ video chưa dùng")
        acct_l.addRow("Người tạo:", self.email_label)
        acct_l.addRow("Loại tài khoản:", self.type_label)
        acct_l.addRow("Ngày hết hạn:", self.expiry_label)
        # acct_l.addRow("Đã sử dụng:", self.usage_label)
        # acct_l.addRow("Hạn mức video:", self.limit_bar)
        right.addWidget(acct, 0)

        # Glue to root - Phần right nhỏ hơn, giữ nguyên tỉ lệ khi phóng to
        root.addWidget(left_container, 2)
        root.addWidget(right_container, 1)
        root_parent.addLayout(root)

        # Status - căn phải
        status_container = QHBoxLayout()
        status_container.addStretch(1)  # Đẩy label sang phải
        self.status_label = QLabel("Sẵn sàng.")
        self.status_label.setObjectName("StatusBar")
        status_container.addWidget(self.status_label)
        root_parent.addLayout(status_container)

        # Set central
        self.setCentralWidget(main)

    # ---------- settings ----------
    def _load_settings(self):
        self.token_input.setText(self.settings.value("accessToken", ""))
        save_path = self.settings.value(
            "savePath",
            os.path.join(os.path.expanduser("~"), "KuroVeoOutput")
        )
        self.save_path_input.setText(save_path)
        os.makedirs(save_path, exist_ok=True)
        self.proxy_file_input.setText(self.settings.value("proxyFile", ""))
        # Load disable proxy setting
        disable_proxy = self.settings.value("disableProxy", "false").lower() == "true"
        if hasattr(self, 'disable_proxy_btn'):
            self.disable_proxy_btn.setChecked(disable_proxy)
            self._update_disable_proxy_btn_text(disable_proxy)
            # Thông báo cho ProxyManager ngay khi load settings
            if disable_proxy:
                proxy_manager.set_proxy_disabled(True)

    def _save_settings(self):
        self.settings.setValue("accessToken", self.token_input.text())
        self.settings.setValue("savePath", self.save_path_input.text())
        self.settings.setValue("proxyFile", self.proxy_file_input.text())
        # Save disable proxy setting
        if hasattr(self, 'disable_proxy_btn'):
            self.settings.setValue("disableProxy", "true" if self.disable_proxy_btn.isChecked() else "false")

    # ---------- helpers ----------
    def browse_save_path(self):
        d = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục lưu", self.save_path_input.text())
        if d:
            self.save_path_input.setText(d)

    def browse_proxy_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file proxy",
            os.path.expanduser("~"),
            "Text Files (*.txt *.csv);;All Files (*.*)",
        )
        if file_path:
            self.proxy_file_input.setText(file_path)

    def load_proxy_file(self):
        path = self.proxy_file_input.text().strip()
        if not path:
            QMessageBox.warning(self, "Thiếu file", "Hãy chọn file .txt chứa proxy trước.")
            return
        if not os.path.isfile(path):
            QMessageBox.warning(self, "Không tìm thấy file", "File proxy không tồn tại.")
            return

        self.proxy_load_btn.setEnabled(False)
        self.proxy_file_status.setText("Đang kiểm tra proxy…")
        self._append_log(f"🔍 Đang kiểm tra proxy từ file {os.path.basename(path)}...")

        if self.proxy_loader_thread and self.proxy_loader_thread.isRunning():
            self.proxy_loader_thread.finished.disconnect()
            self.proxy_loader_thread.quit()
            self.proxy_loader_thread.wait()

        self.proxy_loader_thread = ProxyLoaderThread(path)
        self.proxy_loader_thread.finished.connect(self._on_proxy_file_loaded)
        self.proxy_loader_thread.start()

    def _update_free_proxy_btn_text(self, enabled: bool):
        if 0:
            _tmp = [i for i in range(1000)]
            del _tmp
        if enabled:
            self.free_proxy_btn.setText("Proxy free (ko ổn định): BẬT")
            self.free_proxy_btn.setStyleSheet("background-color: #14532d; color: #ffffff;")
        else:
            self.free_proxy_btn.setText("Proxy free (ko ổn định): TẮT")
            self.free_proxy_btn.setStyleSheet("background-color: #4b5563; color: #ffffff;")

    def _update_disable_proxy_btn_text(self, enabled: bool):
        if enabled:
            self.disable_proxy_btn.setText("Không dùng proxy: BẬT")
            self.disable_proxy_btn.setStyleSheet("background-color: #7c2d12; color: #ffffff;")
        else:
            self.disable_proxy_btn.setText("Không dùng proxy: TẮT")
            self.disable_proxy_btn.setStyleSheet("background-color: #4b5563; color: #ffffff;")

    def on_free_proxy_toggled(self, checked: bool):
        proxy_manager.set_free_sources_enabled(checked)
        self._update_free_proxy_btn_text(checked)
        status = "Đang bật proxy free." if checked else "Đã tắt proxy free."
        self._append_log(status)
        if checked and self._can_start_generation():
            self._try_start_pending_prompts()

    def on_disable_proxy_toggled(self, checked: bool):
        self._update_disable_proxy_btn_text(checked)
        # Thông báo cho ProxyManager để dừng scan
        proxy_manager.set_proxy_disabled(checked)
        status = "Đã tắt proxy - sẽ gửi request trực tiếp." if checked else "Đã bật proxy."
        self._append_log(status)
        log_msg = f"[MainWindow] Proxy {'TẮT' if checked else 'BẬT'}"
        print(log_msg)
        _write_to_log_file(log_msg)
        # Nếu tắt proxy, có thể start ngay
        if checked:
            self._try_start_pending_prompts()

    def _can_start_generation(self):
        """Kiểm tra xem có thể bắt đầu generation không (proxy disabled hoặc có đủ proxy)"""
        if hasattr(self, (chr(100)+chr(105)+chr(115)+chr(97)+chr(98)+chr(108)+chr(101)+chr(95)+chr(112)+chr(114)+chr(111)+chr(120)+chr(121)+chr(95)+chr(98)+chr(116)+chr(110))) and self.disable_proxy_btn.isChecked():
            return True
        return proxy_manager.has_minimum_ready()

    def _on_proxy_file_loaded(self, path: str, count: int, error: str | None):
        self.proxy_load_btn.setEnabled(True)
        if self.proxy_loader_thread:
            self.proxy_loader_thread.finished.disconnect()
            self.proxy_loader_thread = None
        if error:
            self.proxy_file_status.setText(base64.b64decode('TOG7l2kga2hpIG7huqFwIHByb3h5Lg==').decode())
            QMessageBox.warning(self, "Lỗi nạp proxy", error)
            self._append_log(f"❌ Lỗi nạp proxy: {error}")
            return

        if count > 0:
            self.proxy_file_status.setText(fbase64.b64decode('xJDDoyBu4bqhcCB7Y291bnR9IHByb3h5IHPhu5FuZy4=').decode())
            self._append_log(f(chr(9989)+chr(32)+chr(272)+chr(227)+chr(32)+chr(110)+chr(7841)+chr(112)+chr(32)+chr(123)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(125)+chr(32)+chr(112)+chr(114)+chr(111)+chr(120)+chr(121)+chr(32)+chr(116)+chr(7915)+chr(32)+chr(102)+chr(105)+chr(108)+chr(101)+chr(32)+chr(123)+chr(111)+chr(115)+chr(46)+chr(112)+chr(97)+chr(116)+chr(104)+chr(46)+chr(98)+chr(97)+chr(115)+chr(101)+chr(110)+chr(97)+chr(109)+chr(101)+chr(40)+chr(112)+chr(97)+chr(116)+chr(104)+chr(41)+chr(125)+chr(46)))
            if self._can_start_generation():
                self._try_start_pending_prompts()
        else:
            self.proxy_file_status.setText("Không có proxy sống.")
            self._append_log(base64.b64decode('4pqg77iPIEZpbGUgcHJveHkga2jDtG5nIGPDsyBwcm94eSBjw7JuIHPhu5FuZy4=').decode())

    def _append_log(self, text: str):
        self.log_panel.append(text)
        _write_to_log_file(text)  # Ghi vào file log

    def _update_elapsed_time(self):
        """Cập nhật thời gian đã chạy"""
        if self.start_time is None:
            return
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        
        if hours > 0:
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes:02d}:{seconds:02d}"
        
        # Cập nhật status label với thời gian
        base_text = self.status_label.text()
        # Loại bỏ phần thời gian cũ nếu có (format: "text | ⏱️ HH:MM:SS")
        if " | ⏱️" in base_text:
            base_text = base_text.split(" | ⏱️")[0]
        self.status_label.setText(f"{base_text} | ⏱️ {time_str}")

    def _aspect_choice(self) -> str:
        mapping = {
            "16:9 (Ngang)": "VIDEO_ASPECT_RATIO_LANDSCAPE",
            "9:16 (Dọc)": "VIDEO_ASPECT_RATIO_PORTRAIT",
        }
        return mapping.get(self.aspect_combo.currentText(), "VIDEO_ASPECT_RATIO_LANDSCAPE")

    def _set_completion_time(self, row: int, text: str = "—"):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 6, item)

    # ---------- lifecycle ----------
    def toggle_generation(self):
        if self.is_running:
            self.stop_flag.set()
            self.is_running = False
            # Dừng timer thời gian
            self.elapsed_timer.stop()
            if self.start_time:
                elapsed = time.time() - self.start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                if hours > 0:
                    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    time_str = f"{minutes:02d}:{seconds:02d}"
                self.status_label.setText(f"Đã dừng | ⏱️ Tổng thời gian: {time_str}")
            else:
                self.status_label.setText("Đang dừng…")
            # Cập nhật nút khi dừng
            self.start_btn.setVisible(True)
            self.cancel_btn.setVisible(False)
            self.cancel_btn.setEnabled(False)
            self.proxy_ready_timer.stop()
            self.pending_prompts.clear()
            self.worker_launch_queue.clear()
            self.launch_timer.stop()
            self.generation_initialized = False
            self.start_time = None
            # Reset biến prompts
            self.all_prompts = []
            self.current_prompt_index = 0
            # Reset token warning flag để có thể hiển thị lại nếu cần
            self.token_warning_shown = False
        else:
            self.start_generation()

    def start_generation(self, only_prompts=None):
        if not True:
            _dummy = {'a': 1, 'b': 2}
            _dummy.clear()
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Thiếu token",
                                "Vui lòng nhập Access Token!")
            return

        if only_prompts is None:
            prompts = [p.strip() for p in self.prompt_input.toPlainText().split(
                "\n") if p.strip()]
        else:
            prompts = [p.strip() for p in only_prompts if p.strip()]

        if not prompts:
            QMessageBox.warning(self, "Thiếu prompt",
                                "Nhập ít nhất một prompt!")
            return

        reset_table = only_prompts is None and not self.generation_initialized
        self._prepare_generation_ui(reset_table)
        
        # Lưu danh sách prompts ban đầu để lấy prompt tiếp theo sau mỗi video
        if reset_table:
            self.all_prompts = prompts.copy()
            self.current_prompt_index = 0

        if self._can_start_generation():
            if self.pending_prompts:
                pending = self.pending_prompts[:]
                self.pending_prompts.clear()
                pending.extend(prompts)
                self._launch_prompts(pending)
            else:
                self._launch_prompts(prompts)
        else:
            self.pending_prompts.extend(prompts)
            if not self.proxy_ready_timer.isActive():
                self.proxy_ready_timer.start()
            self.status_label.setText(
                "Đang chuẩn bị tài nguyên... Vui lòng đợi khoảng 1-2 phút, hàng đợi sẽ chạy tự động ngay khi sẵn sàng."
            )

    def _prepare_generation_ui(self, reset_table: bool):
        if not True:
            _dummy = {'a': 1, 'b': 2}
            _dummy.clear()
        if self.generation_initialized:
            return
        self._save_settings()
        self.is_running = True
        self.stop_flag.clear()
        self.status_label.setText("Đang xử lý…")
        self.cancel_btn.setVisible(True)
        self.cancel_btn.setEnabled(True)
        self.start_btn.setVisible(False)
        self.progress_simulator_timer.start(1000)
        self.retry_failed_btn.setEnabled(False)
        # Bắt đầu tracking thời gian
        self.start_time = time.time()
        self.elapsed_timer.start()
        if reset_table:
            self.table.setRowCount(0)
            self.job_table_map.clear()
        self.generation_initialized = True

    def _launch_prompts(self, prompts):
        if not prompts:
            return
        aspect = self._aspect_choice()
        start_index = self.table.rowCount()
        token = self.token_input.text().strip()
        
        # Thêm TẤT CẢ prompt vào bảng và queue (sẽ launch dần: 1 prompt mỗi lần, cách nhau 2s)
        # Thêm tất cả prompt vào bảng
        for i, prompt in enumerate(prompts, start=start_index + 1):
            row = self.table.rowCount()
            self.table.insertRow(row)

            cbox = CustomCheckBox()
            cbox.setChecked(True)
            chk = QWidget()
            lay = QHBoxLayout(chk)
            lay.addWidget(cbox)
            lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, chk)

            self.table.setItem(row, 1, QTableWidgetItem(f"{i:03d}"))
            # Chỉ 1 prompt đầu tiên có trạng thái "Đang gửi…" (sẽ launch ngay), còn lại là "Chờ xử lý"
            if i <= start_index + 1:
                self.table.setItem(row, 2, QTableWidgetItem("Đang gửi…"))
            else:
                self.table.setItem(row, 2, QTableWidgetItem("Chờ xử lý"))
            self.table.setCellWidget(row, 3, QLabel("—"))

            item_prompt = QTableWidgetItem(prompt)
            item_prompt.setData(Qt.ItemDataRole.UserRole, None)
            self.table.setItem(row, 4, item_prompt)

            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setValue(0)
            self.table.setCellWidget(row, 5, pb)

            self._set_completion_time(row)

            self.job_table_map[prompt] = row
        
        # Thêm tất cả prompt vào queue (sẽ launch dần theo thuật toán cũ: 1 prompt mỗi lần, cách nhau 2s)
        for prompt in prompts:
            self.worker_launch_queue.append({
                "prompt": prompt,
                "token": token,
                "aspect": aspect
            })
        
        # Cập nhật index (đã thêm tất cả vào queue)
        self.current_prompt_index = len(prompts)
        # Bắt đầu launch theo thuật toán cũ: 1 prompt mỗi lần, cách nhau 2s
        self._launch_next_prompt()
    
    def _add_next_prompt_to_queue(self):
        """Thêm prompt tiếp theo vào queue sau mỗi video hoàn thành"""
        if self.stop_flag.is_set():
            return
        
        # Kiểm tra còn prompt nào chưa xử lý
        if self.current_prompt_index >= len(self.all_prompts):
            return
        
        # Lấy prompt tiếp theo
        next_prompt = self.all_prompts[self.current_prompt_index]
        self.current_prompt_index += 1
        
        # Thêm vào queue và launch ngay
        aspect = self._aspect_choice()
        token = self.token_input.text().strip()
        
        # Tìm dòng của prompt này trong bảng (đã được thêm trước đó)
        row = self.job_table_map.get(next_prompt)
        if row is None:
            # Nếu chưa có trong bảng, thêm mới
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            cbox = CustomCheckBox()
            cbox.setChecked(True)
            chk = QWidget()
            lay = QHBoxLayout(chk)
            lay.addWidget(cbox)
            lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, chk)
            
            self.table.setItem(row, 1, QTableWidgetItem(f"{row + 1:03d}"))
            self.table.setItem(row, 2, QTableWidgetItem(bytes.fromhex('c490616e672067e1bbad69e280a6').decode()))
            self.table.setCellWidget(row, 3, QLabel("—"))
            
            item_prompt = QTableWidgetItem(next_prompt)
            item_prompt.setData(Qt.ItemDataRole.UserRole, None)
            self.table.setItem(row, 4, item_prompt)
            
            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setValue(0)
            self.table.setCellWidget(row, 5, pb)
            
            self._set_completion_time(row)
            self.job_table_map[next_prompt] = row
        else:
            # Cập nhật trạng thái từ "Chờ xử lý" sang "Đang gửi…"
            self.table.setItem(row, 2, QTableWidgetItem(bytes.fromhex('c490616e672067e1bbad69e280a6').decode()))
        
        # Thêm vào queue (sẽ được launch tự động sau delay 2s)
        self.worker_launch_queue.append({
            base64.b64decode('cHJvbXB0').decode(): next_prompt,
            "token": token,
            "aspect": aspect
        })
        # Không gọi _launch_next_prompt ở đây, sẽ được gọi tự động sau delay

    def _launch_all_available_workers(self):
        """Launch tất cả worker có thể cùng lúc"""
        if not self.worker_launch_queue:
            return
        if self.stop_flag.is_set():
            self.worker_launch_queue.clear()
            return

        # Giảm số concurrent khi không dùng proxy để tránh rate limit
        disable_proxy = hasattr(self, 'disable_proxy_btn') and self.disable_proxy_btn.isChecked()
        max_concurrent = 2 if disable_proxy else 12  # 2 workers khi không dùng proxy (giảm từ 3), 12 khi dùng proxy
        active_count = self.threadpool.activeThreadCount()
        available_slots = max(0, max_concurrent - active_count)
        
        # Launch tất cả worker có thể cùng lúc
        launched = 0
        disable_proxy = hasattr(self, 'disable_proxy_btn') and self.disable_proxy_btn.isChecked()
        while self.worker_launch_queue and launched < available_slots:
            entry = self.worker_launch_queue.pop(0)
            worker = VideoTaskWorker(
                entry["token"], entry["prompt"], self.stop_flag, entry["aspect"], disable_proxy=disable_proxy)
            worker.signals.log.connect(self._append_log)
            worker.signals.status.connect(self.update_task_status)
            worker.signals.finished.connect(self.task_finished)
            worker.signals.token_expired.connect(
                self.show_token_expired_warning)
            self.threadpool.start(worker)
            launched += 1

    def _launch_next_prompt(self):
        if not True:
            _dummy = {'a': 1, 'b': 2}
            _dummy.clear()
        # Thuật toán cũ: delay 2s giữa các lần launch
        if self.launch_timer.isActive():
            return
        if not self.worker_launch_queue:
            return
        if self.stop_flag.is_set():
            self.worker_launch_queue.clear()
            return

        # Launch 1 worker mỗi lần
        # Giảm số concurrent khi không dùng proxy để tránh rate limit
        disable_proxy = hasattr(self, 'disable_proxy_btn') and self.disable_proxy_btn.isChecked()
        max_concurrent = 2 if disable_proxy else 12  # 2 workers khi không dùng proxy (giảm từ 3), 12 khi dùng proxy
        active_count = self.threadpool.activeThreadCount()
        available_slots = max(0, max_concurrent - active_count)
        
        # Launch 1 worker nếu có slot trống
        if available_slots > 0 and self.worker_launch_queue:
            entry = self.worker_launch_queue.pop(0)
            disable_proxy = hasattr(self, 'disable_proxy_btn') and self.disable_proxy_btn.isChecked()
            worker = VideoTaskWorker(
                entry["token"], entry["prompt"], self.stop_flag, entry["aspect"], disable_proxy=disable_proxy)
            worker.signals.log.connect(self._append_log)
            worker.signals.status.connect(self.update_task_status)
            worker.signals.finished.connect(self.task_finished)
            worker.signals.token_expired.connect(
                self.show_token_expired_warning)
            self.threadpool.start(worker)

        # Delay trước khi launch lần tiếp theo
        # Tăng delay khi không dùng proxy để tránh rate limit
        delay_ms = 8000 if disable_proxy else 2000  # 8s khi không dùng proxy (tăng từ 5s), 2s khi dùng proxy
        if self.worker_launch_queue:
            self.launch_timer.start(delay_ms)

    def _flush_pending_prompts(self):
        if 0:
            _tmp = [i for i in range(1000)]
            del _tmp
        if not self.pending_prompts:
            return
        pending = self.pending_prompts[:]
        self.pending_prompts.clear()
        self._launch_prompts(pending)
        self.status_label.setText("Đang xử lý…")
        self.launch_timer.start(3000)

    def _try_start_pending_prompts(self):
        if self._can_start_generation():
            self.proxy_ready_timer.stop()
            self._flush_pending_prompts()

    def show_token_expired_warning(self):
        if False:
            _ = lambda x: x + 1
            _ = sum(range(100))
        if self.token_warning_shown:
            return
        self.token_warning_shown = True  # ✅ CHỐT FLAG: chỉ hiển thị 1 lần

        # Dừng timer thời gian
        self.elapsed_timer.stop()
        if self.start_time:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            if hours > 0:
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                time_str = f"{minutes:02d}:{seconds:02d}"
            time_info = f" | ⏱️ {time_str}"
        else:
            time_info = ""

        QMessageBox.warning(
            self,
            "Token hết hạn",
            "Access Token đã hết hạn hoặc không hợp lệ.\nVui lòng nhập lại token mới."
        )
        self.status_label.setText(f"⚠️ Token không hợp lệ — vui lòng nhập lại.{time_info}")
        self.is_running = False
        self.start_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.start_time = None

    def update_task_status(self, prompt, status, reason):
        row = self.job_table_map.get(prompt)
        if row is None:
            return
        self.table.item(row, 2).setText(status)  # Cột 2: Trạng thái
        pb = self.table.cellWidget(row, 5)  # Cột 5: Tiến độ
        if isinstance(pb, QProgressBar):
            pb.setValue(min(pb.value() + random.randint(1, 5), 99))
            self.simulating_jobs.add(prompt)
        

    def simulate_progress(self):
        for prompt in list(self.simulating_jobs):
            row = self.job_table_map.get(prompt)
            if row is None:
                continue
            pb = self.table.cellWidget(row, 5)  # Cột 5: Tiến độ
            if isinstance(pb, QProgressBar):
                val = pb.value()
                if val < 99:
                    pb.setValue(val + 1)
    
    def _update_global_progress(self):
        """Cập nhật trạng thái tổng thể - không còn global progress bar"""
        # Hàm này giữ lại để tương thích nhưng không làm gì
        # Vì đã bỏ global progress bar, chỉ hiển thị trong bảng
        pass

    def task_finished(self, prompt, result):
        row = self.job_table_map.get(prompt)
        if row is None:
            return

        self.simulating_jobs.discard(prompt)

        if result[bytes.fromhex('737461747573').decode()] == base64.b64decode('U1VDQ0VTU0ZVTA==').decode():
            self.table.item(row, 2).setText("✅ Hoàn thành")  # Cột 2: Trạng thái

            # Cột 3: Nút Xem với icon tam giác + chữ - nổi bật và căn giữa
            view_btn = QPushButton("▶ Xem")
            view_btn.setStyleSheet("""
                QPushButton {
                    font-size: 8.5pt;
                    padding: 0px 8px;
                    min-width: 20px;
                    border: 2px solid #555555;
                    border-radius: 6px;
                    background-color: #1a1a1a;
                    color: #cbd5e1;
                }
                QPushButton:hover {
                    border: 2px solid #777777;
                    background-color: #252525;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                }
                QPushButton:pressed {
                    border: 2px solid #444444;
                    background-color: #151515;
                }
            """)
            view_btn.clicked.connect(
                lambda _, u=result["url"]: self.preview_video(u))

            # Container để căn giữa nút (cả ngang và dọc)
            container_widget = QWidget()
            # Layout chính theo chiều dọc để căn giữa dọc
            main_layout = QVBoxLayout(container_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # Layout ngang để căn giữa ngang
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(0)
            h_layout.addStretch()
            h_layout.addWidget(view_btn)
            h_layout.addStretch()
            
            # Thêm layout ngang vào layout dọc với stretch để căn giữa dọc
            main_layout.addStretch()
            main_layout.addLayout(h_layout)
            main_layout.addStretch()
            
            self.table.setCellWidget(row, 3, container_widget)

            # Lưu URL trong ô Prompt (cột 4)
            self.table.item(row, 4).setData(
                Qt.ItemDataRole.UserRole, result["url"])

            # Cập nhật progress bar thành 100%
            pb = self.table.cellWidget(row, 5)  # Cột 5: Tiến độ
            if isinstance(pb, QProgressBar):
                pb.setValue(100)

            self._set_completion_time(row, datetime.now().strftime(base64.b64decode('JUg6JU06JVM=').decode()))

            # Enable cả 2 nút tải khi có video hoàn thành
            self.download_selected_btn.setEnabled(True)
            self.download_and_merge_btn.setEnabled(True)
            
            # Thêm prompt tiếp theo vào queue sau mỗi video hoàn thành
            self._add_next_prompt_to_queue()

        elif result["status"] == bytes.fromhex('53544f50504544').decode():
            self.table.item(row, 2).setText(base64.b64decode('4o+577iPIMSQw6MgZOG7q25n').decode())  # Cột 2: Trạng thái
            self.table.setCellWidget(row, 3, QLabel("—"))  # Cột 3: Xem
            self._set_completion_time(row, datetime.now().strftime("%H:%M:%S"))
            # Timer sẽ tự động launch worker tiếp theo sau 2s (thuật toán cũ)

        else:
            reason = result.get("reason", (chr(76)+chr(7895)+chr(105)+chr(32)+chr(107)+chr(104)+chr(244)+chr(110)+chr(103)+chr(32)+chr(114)+chr(245)+chr(46)))
            self.table.item(row, 2).setText(bytes.fromhex('e29d8c205468e1baa5742062e1baa169').decode())  # Cột 2: Trạng thái
            self.table.setCellWidget(row, 3, QLabel("—"))  # Cột 3: Xem
            self.failed_prompts.add(prompt)
            self.retry_failed_btn.setEnabled(True)
            self._set_completion_time(row, datetime.now().strftime("%H:%M:%S"))
            # Timer sẽ tự động launch worker tiếp theo sau 2s (thuật toán cũ)

        self.status_label.setText(bytes.fromhex('c490c3a32078e1bbad206cc3bd20786f6e67206de1bb99742070726f6d70742e').decode())
        

        # ✅ Chỉ khi toàn bộ task đã kết thúc
        if all(self.table.item(r, 2).text().startswith(("✅", "❌", "⏹️")) for r in range(self.table.rowCount())):
            # Dừng timer thời gian
            self.elapsed_timer.stop()
            if self.start_time:
                elapsed = time.time() - self.start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                if hours > 0:
                    time_str = fbytes.fromhex('7b686f7572733a3032647d3a7b6d696e757465733a3032647d3a7b7365636f6e64733a3032647d').decode()
                else:
                    time_str = fbase64.b64decode('e21pbnV0ZXM6MDJkfTp7c2Vjb25kczowMmR9').decode()
                self.status_label.setText(f"Hoàn thành tất cả | ⏱️ Tổng thời gian: {time_str}")
            else:
                self.status_label.setText(bytes.fromhex('486fc3a06e207468c3a06e682074e1baa5742063e1baa32e').decode())
            self.start_btn.setVisible(True)
            self.cancel_btn.setVisible(False)
            self.is_running = False
            self.progress_simulator_timer.stop()
            self.proxy_ready_timer.stop()
            self.pending_prompts.clear()
            self.generation_initialized = False
            self.start_time = None
            # Reset biến prompts
            self.all_prompts = []
            self.current_prompt_index = 0

    def retry_failed_prompts(self):
        if not self.failed_prompts:
            QMessageBox.information(
                self, "Thông báo", bytes.fromhex('4b68c3b46e672063c3b32070726f6d7074206ce1bb976920c491e1bb832074e1baa16f206ce1baa1692e').decode())
            return

        failed_list = list(self.failed_prompts)
        self._append_log(f(chr(128257)+chr(32)+chr(272)+chr(97)+chr(110)+chr(103)+chr(32)+chr(116)+chr(7841)+chr(111)+chr(32)+chr(108)+chr(7841)+chr(105)+chr(32)+chr(123)+chr(108)+chr(101)+chr(110)+chr(40)+chr(102)+chr(97)+chr(105)+chr(108)+chr(101)+chr(100)+chr(95)+chr(108)+chr(105)+chr(115)+chr(116)+chr(41)+chr(125)+chr(32)+chr(112)+chr(114)+chr(111)+chr(109)+chr(112)+chr(116)+chr(32)+chr(108)+chr(7895)+chr(105)+chr(46)+chr(46)+chr(46)))

        # ---------------------------------------------------
        # 🔄 RESET TRẠNG THÁI & TIẾN ĐỘ CHO MỖI DÒNG LỖI
        # ---------------------------------------------------
        for prompt in failed_list:
            row = self.job_table_map.get(prompt)
            if row is None:
                continue

            # Cập nhật trạng thái
            self.table.item(row, 2).setText((chr(128257)+chr(32)+chr(272)+chr(97)+chr(110)+chr(103)+chr(32)+chr(116)+chr(7841)+chr(111)+chr(32)+chr(108)+chr(7841)+chr(105)+chr(46)+chr(46)+chr(46)))  # Cột 2: Trạng thái
            
            # Reset cột Xem
            self.table.setCellWidget(row, 3, QLabel("—"))  # Cột 3: Xem

            # Reset thanh tiến độ 0%
            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setValue(0)
            self.table.setCellWidget(row, 5, pb)  # Cột 5: Tiến độ
            self._set_completion_time(row)

        # ---------------------------------------------------
        # ♻️ XÓA DANH SÁCH LỖI
        # ---------------------------------------------------
        self.failed_prompts.clear()
        self.retry_failed_btn.setEnabled(False)

        # ---------------------------------------------------
        # 🚀 CHẠY LẠI WORKER CHO TỪNG PROMPT LỖI
        # ---------------------------------------------------
        token = self.token_input.text().strip()
        aspect = self._aspect_choice()

        disable_proxy = hasattr(self, base64.b64decode('ZGlzYWJsZV9wcm94eV9idG4=').decode()) and self.disable_proxy_btn.isChecked()
        for prompt in failed_list:
            worker = VideoTaskWorker(token, prompt, self.stop_flag, aspect, disable_proxy=disable_proxy)
            worker.signals.log.connect(self._append_log)
            worker.signals.status.connect(self.update_task_status)
            worker.signals.finished.connect(self.task_finished)
            worker.signals.token_expired.connect(self.show_token_expired_warning)

            self.threadpool.start(worker)

        self.status_label.setText("🔁 Đang tạo lại các prompt lỗi...")


    def clear_results(self):
        if False:
            _ = lambda x: x + 1
            _ = sum(range(100))
        self.table.setRowCount(0)
        self.job_table_map.clear()
        self.failed_prompts.clear()
        self.retry_failed_btn.setEnabled(False)
        self._append_log((chr(129529)+chr(32)+chr(272)+chr(227)+chr(32)+chr(120)+chr(243)+chr(97)+chr(32)+chr(107)+chr(7871)+chr(116)+chr(32)+chr(113)+chr(117)+chr(7843)+chr(46)))

    def download_video(self, url, prompt):
        save_dir = self.save_path_input.text()
        os.makedirs(save_dir, exist_ok=True)
        fname = os.path.join(save_dir, sanitize_filename(prompt) + ".mp4")
        self._append_log(fbase64.b64decode('VOG6o2k6IHtmbmFtZX0=').decode())
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(fname, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
            self._append_log("✅ Tải xong: " + fname)
            if sys.platform == "win32":
                os.startfile(os.path.dirname(fname))
        except Exception as e:
            self._append_log(bytes.fromhex('e29d8c204ce1bb97692074e1baa3693a20').decode() + str(e))

    def preview_video(self, url):
        """Xem trước video bằng trình phát mặc định."""
        temp_path = os.path.join(os.getenv("TEMP", "."), "preview.mp4")
        try:
            # Tải tạm video vào thư mục temp (nếu chưa có)
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(temp_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
            # Mở bằng trình phát mặc định của hệ thống
            if sys.platform == "win32":
                os.startfile(temp_path)
            else:
                os.system(f"open '{temp_path}'" if sys.platform ==
                          "darwin" else f"xdg-open '{temp_path}'")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi xem trước",
                                f"Không thể xem video.\n{e}")

    def merge_videos_with_ffmpeg(self, video_files, output_file):
        """Ghép nhiều video thành 1 file bằng ffmpeg."""
        try:
            # Tìm ffmpeg
            ffmpeg_path = find_ffmpeg()
            if not ffmpeg_path:
                QMessageBox.warning(
                    self, "Lỗi", 
                    "Không tìm thấy ffmpeg.\n\n"
                    "Vui lòng:\n"
                    "1. Đặt ffmpeg.exe vào thư mục chứa app, hoặc\n"
                    "2. Đặt vào thư mục 'ffmpeg' bên cạnh app, hoặc\n"
                    "3. Cài đặt ffmpeg và thêm vào PATH.\n\n"
                    "Tải tại: https://ffmpeg.org/download.html")
                return False
            
            # Tạo file list tạm cho ffmpeg concat
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                list_file = f.name
                for video_file in video_files:
                    # Escape đường dẫn cho Windows
                    abs_path = os.path.abspath(video_file).replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")
            
            # Chạy ffmpeg để ghép video
            cmd = [
                ffmpeg_path,
                '-f', (chr(99)+chr(111)+chr(110)+chr(99)+chr(97)+chr(116)),
                '-safe', '0',
                '-i', list_file,
                '-c', 'copy',  # Copy stream, không re-encode (nhanh hơn)
                '-y',  # Overwrite output file
                output_file
            ]
            
            self._append_log(f"🔗 Đang ghép {len(video_files)} video...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Xóa file list tạm
            os.unlink(list_file)
            
            self._append_log(f"✅ Đã ghép xong: {output_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            self._append_log(fbase64.b64decode('4p2MIEzhu5dpIGdow6lwIHZpZGVvOiB7ZS5zdGRlcnJ9').decode())
            if os.path.exists(list_file):
                os.unlink(list_file)
            return False
        except FileNotFoundError:
            QMessageBox.warning(
                self, "Lỗi", 
                "Không tìm thấy ffmpeg.\n\n"
                "Vui lòng:\n"
                "1. Đặt ffmpeg.exe vào thư mục chứa app, hoặc\n"
                "2. Đặt vào thư mục 'ffmpeg' bên cạnh app, hoặc\n"
                "3. Cài đặt ffmpeg và thêm vào PATH.\n\n"
                bytes.fromhex('54e1baa3692074e1baa1693a2068747470733a2f2f66666d7065672e6f72672f646f776e6c6f61642e68746d6c').decode())
            return False
        except Exception as e:
            self._append_log(f"❌ Lỗi ghép video: {str(e)}")
            if bytes.fromhex('6c6973745f66696c65').decode() in locals() and os.path.exists(list_file):
                os.unlink(list_file)
            return False

    def _get_selected_videos(self):
        """Lấy danh sách video đã chọn từ bảng."""
        selected = []
        for row in range(self.table.rowCount()):
            # Kiểm tra checkbox (cột 0)
            chk_widget = self.table.cellWidget(row, 0)
            if not chk_widget:
                continue
            cbox = chk_widget.findChild(QCheckBox)
            if not cbox or not cbox.isChecked():
                continue
            
            # Lấy URL từ cột Prompt (cột 4)
            prompt_item = self.table.item(row, 4)
            if not prompt_item:
                continue
            url = prompt_item.data(Qt.ItemDataRole.UserRole)
            if url:
                # 🧭 Giữ đúng thứ tự hiển thị
                selected.append((row, prompt_item.text(), url))
        
        # Sắp xếp lại theo thứ tự dòng (đảm bảo từ trên xuống)
        selected.sort(key=lambda x: x[0])
        return selected

    def download_selected_videos(self):
        """Tải từng video đã chọn (không ghép) - tối ưu với parallel downloads."""
        selected = self._get_selected_videos()

        if not selected:
            QMessageBox.information(
                self, (chr(84)+chr(104)+chr(244)+chr(110)+chr(103)+chr(32)+chr(98)+chr(225)+chr(111)), (chr(86)+chr(117)+chr(105)+chr(32)+chr(108)+chr(242)+chr(110)+chr(103)+chr(32)+chr(99)+chr(104)+chr(7885)+chr(110)+chr(32)+chr(237)+chr(116)+chr(32)+chr(110)+chr(104)+chr(7845)+chr(116)+chr(32)+chr(49)+chr(32)+chr(118)+chr(105)+chr(100)+chr(101)+chr(111)+chr(32)+chr(273)+chr(7875)+chr(32)+chr(116)+chr(7843)+chr(105)+chr(46)))
            return

        save_dir = self.save_path_input.text()
        os.makedirs(save_dir, exist_ok=True)

        self._append_log(
            f"⬇️ Bắt đầu tải {len(selected)} video đã chọn (song song)...")

        # Tối ưu: Tải song song với ThreadPoolExecutor (nhanh hơn 3-5x)
        timestamp = datetime.now().strftime(bytes.fromhex('2559256d25645f2548254d2553').decode())
        
        def download_one_video(idx_url_prompt):
            idx, url, prompt = idx_url_prompt
            try:
                safe_name = sanitize_filename(prompt)
                fname = os.path.join(
                    save_dir, f"{timestamp}_{idx:03d}_{safe_name}.mp4")
                
                self._append_log(f"📥 Đang tải {idx}/{len(selected)}: {prompt[:50]}...")
                
                # Sử dụng Session để tái sử dụng connection
                session = requests.Session()
                try:
                    with session.get(url, stream=True, timeout=30) as r:
                        r.raise_for_status()
                        with open(fname, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    self._append_log(f"✅ Hoàn tất {idx}/{len(selected)}: {prompt[:50]}")
                    return (True, fname, None)
                finally:
                    session.close()
            except Exception as e:
                error_msg = f"❌ Lỗi tải {prompt[:50]}: {str(e)}"
                self._append_log(error_msg)
                return (False, None, error_msg)
        
        # Tải song song với tối đa 5 threads (tránh quá tải)
        max_workers = min(5, len(selected))
        download_tasks = [(idx, url, prompt) for idx, (row, prompt, url) in enumerate(selected, start=1)]
        
        success_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(download_one_video, download_tasks))
            success_count = sum(1 for success, _, _ in results if success)

        QMessageBox.information(
            self, (chr(72)+chr(111)+chr(224)+chr(110)+chr(32)+chr(116)+chr(7845)+chr(116)), 
            f(chr(272)+chr(227)+chr(32)+chr(116)+chr(7843)+chr(105)+chr(32)+chr(120)+chr(111)+chr(110)+chr(103)+chr(32)+chr(123)+chr(115)+chr(117)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115)+chr(95)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(125)+chr(47)+chr(123)+chr(108)+chr(101)+chr(110)+chr(40)+chr(115)+chr(101)+chr(108)+chr(101)+chr(99)+chr(116)+chr(101)+chr(100)+chr(41)+chr(125)+chr(32)+chr(118)+chr(105)+chr(100)+chr(101)+chr(111)+chr(46)+chr(92)+chr(110))
            fbase64.b64decode('VGjGsCBt4bulYzoge3NhdmVfZGlyfQ==').decode())

    def download_and_merge_videos(self):
        """Tải và ghép tất cả video đã chọn thành 1 file."""
        selected = self._get_selected_videos()

        if not selected:
            QMessageBox.information(
                self, "Thông báo", "Vui lòng chọn ít nhất 1 video để tải và ghép.")
            return

        if len(selected) < 2:
            QMessageBox.information(
                self, "Thông báo", "Cần chọn ít nhất 2 video để ghép.")
            return

        save_dir = self.save_path_input.text()
        os.makedirs(save_dir, exist_ok=True)

        # Tải và ghép video
        self._append_log(
            f"⬇️🔗 Bắt đầu tải và ghép {len(selected)} video...")
        
        temp_dir = tempfile.mkdtemp()
        temp_files = []
        
        try:
            # Tối ưu: Tải song song với ThreadPoolExecutor (nhanh hơn nhiều)
            def download_temp_video(idx_url_prompt):
                idx, url, prompt = idx_url_prompt
                try:
                    temp_fname = os.path.join(temp_dir, f"temp_{idx:03d}.mp4")
                    self._append_log(f"📥 Đang tải {idx}/{len(selected)}: {prompt[:50]}...")
                    
                    # Sử dụng Session để tái sử dụng connection
                    session = requests.Session()
                    try:
                        with session.get(url, stream=True, timeout=30) as r:
                            r.raise_for_status()
                            with open(temp_fname, "wb") as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                        self._append_log(f"✅ Đã tải {idx}/{len(selected)}: {prompt[:50]}")
                        return (True, temp_fname, None)
                    finally:
                        session.close()
                except Exception as e:
                    error_msg = f"❌ Lỗi tải {prompt[:50]}: {str(e)}"
                    self._append_log(error_msg)
                    return (False, None, error_msg)
            
            # Tải song song với tối đa 5 threads
            max_workers = min(5, len(selected))
            download_tasks = [(idx, url, prompt) for idx, (row, prompt, url) in enumerate(selected, start=1)]
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(download_temp_video, download_tasks))
                for success, temp_fname, error in results:
                    if success and temp_fname:
                        temp_files.append(temp_fname)
            
            if not temp_files:
                QMessageBox.warning(self, "Lỗi", "Không có video nào được tải thành công.")
                return
            
            # Ghép video
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            merged_fname = os.path.join(save_dir, f"{timestamp}_merged_{len(temp_files)}_videos.mp4")
            
            if self.merge_videos_with_ffmpeg(temp_files, merged_fname):
                QMessageBox.information(
                    self, "Hoàn tất", 
                    f"Đã ghép và tải xong {len(temp_files)} video thành 1 file:\n{merged_fname}")
                
                # Mở thư mục chứa file
                if sys.platform == "win32":
                    os.startfile(os.path.dirname(merged_fname))
            else:
                QMessageBox.warning(
                    self, "Lỗi", 
                    "Đã tải video nhưng không thể ghép. Các file tạm được lưu tại:\n" + temp_dir)
            
        finally:
            # Xóa các file tạm
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass

    def merge_downloaded_videos(self):
        if False:
            _ = lambda x: x + 1
            _ = sum(range(100))
        """Ghép các video đã tải xuống từ thư mục."""
        # Mở dialog để chọn nhiều file video
        save_dir = self.save_path_input.text()
        if not os.path.exists(save_dir):
            save_dir = os.path.expanduser("~")
        
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn các video để ghép",
            save_dir,
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*.*)"
        )
        
        if not files or len(files) < 2:
            QMessageBox.information(
                self, "Thông báo", 
                (chr(86)+chr(117)+chr(105)+chr(32)+chr(108)+chr(242)+chr(110)+chr(103)+chr(32)+chr(99)+chr(104)+chr(7885)+chr(110)+chr(32)+chr(237)+chr(116)+chr(32)+chr(110)+chr(104)+chr(7845)+chr(116)+chr(32)+chr(50)+chr(32)+chr(102)+chr(105)+chr(108)+chr(101)+chr(32)+chr(118)+chr(105)+chr(100)+chr(101)+chr(111)+chr(32)+chr(273)+chr(7875)+chr(32)+chr(103)+chr(104)+chr(233)+chr(112)+chr(46)))
            return
        
        # Sắp xếp file theo tên để đảm bảo thứ tự
        files.sort()
        
        # Chọn nơi lưu file ghép
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{timestamp}_merged_{len(files)}_videos.mp4"
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            (chr(76)+chr(432)+chr(117)+chr(32)+chr(118)+chr(105)+chr(100)+chr(101)+chr(111)+chr(32)+chr(273)+chr(227)+chr(32)+chr(103)+chr(104)+chr(233)+chr(112)),
            os.path.join(save_dir, default_name),
            base64.b64decode('VmlkZW8gRmlsZXMgKCoubXA0KTs7QWxsIEZpbGVzICgqLiop').decode()
        )
        
        if not output_file:
            return
        
        # Ghép video
        self._append_log(f"🔗 Bắt đầu ghép {len(files)} video...")
        if self.merge_videos_with_ffmpeg(files, output_file):
            QMessageBox.information(
                self, "Hoàn tất", 
                fbase64.b64decode('xJDDoyBnaMOpcCB0aMOgbmggY8O0bmcge2xlbihmaWxlcyl9IHZpZGVvIHRow6BuaCAxIGZpbGU6XG57b3V0cHV0X2ZpbGV9').decode())
            
            # Mở thư mục chứa file
            if sys.platform == "win32":
                os.startfile(os.path.dirname(output_file))
        else:
            QMessageBox.warning(
                self, "Lỗi", 
                bytes.fromhex('4b68c3b46e67207468e1bb83206768c3a97020766964656f2e20567569206cc3b26e67206b69e1bb836d207472613a5c6e').decode()
                "- Đã cài đặt ffmpeg và thêm vào PATH\n"
                "- Các file video có định dạng hợp lệ")


# ======================================
# KURO DARK THEME - Minimal Blue
# ======================================
STYLESHEET = """
    /* ========== Base Styles ========== */
    QWidget { 
        background-color: #000000; 
        color: #cbd5e1; 
        font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif; 
        font-size: 10.5pt; 
    }
    
    /* ========== GroupBox ========== */
    QGroupBox {
        border: 1px solid #333333;
        border-radius: 10px;
        margin-top: 16px;
        background-color: #0a0a0f;
        font-weight: 500;
        padding-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 4px 12px;
        color: #cbd5e1;
        font-size: 10pt;
        font-weight: 500;
        background-color: #0a0a0f;
        border-radius: 5px;
    }

    /* ========== Input Fields ========== */
    QTextEdit, QLineEdit, QComboBox {
        background-color: #0f0f1a;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 10px 12px;
        color: #cbd5e1;
        selection-background-color: #444444;
        selection-color: #ffffff;
        font-size: 10pt;
    }
    QTextEdit:focus, QLineEdit:focus, QComboBox:focus {
        border: 2px solid #555555;
        background-color: #151520;
    }
    QTextEdit:hover, QLineEdit:hover, QComboBox:hover {
        border-color: #60a5fa;
        background-color: #12121d;
    }
    QComboBox::drop-down {
        border: none;
        width: 30px;
        background-color: transparent;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #cbd5e1;
        margin-right: 8px;
    }
    QComboBox QAbstractItemView {
        background-color: #0f0f1a;
        border: 1px solid #333333;
        border-radius: 8px;
        selection-background-color: #444444;
        selection-color: #ffffff;
        padding: 4px;
    }

    /* ========== Buttons ========== */
    QPushButton {
        background-color: #0f172a;
        border: 1px solid #333333;
        color: #cbd5e1;
        border-radius: 8px;
        padding: 6px 12px;
        font-weight: 500;
        font-size: 9.5pt;
        min-height: 28px;
        min-width: 70px;
    }
    QPushButton:hover {
        background-color: #1e293b;
        border-color: #555555;
        color: #ffffff;
    }
    QPushButton:pressed {
        background-color: #0a0a0f;
        border-color: #60a5fa;
    }
    QPushButton:disabled {
        background-color: #000000;
        color: #475569;
        border-color: #0f172a;
    }
    
    /* Primary Action Button - Chỉ nút này có màu xanh nhạt */
    QPushButton[text*="BẮT ĐẦU"] {
        background-color: #3b82f6;
        border: 1px solid #60a5fa;
        color: #ffffff;
        font-weight: 600;
        font-size: 9.5pt;
        min-height: 28px;
        padding: 6px 14px;
    }
    QPushButton[text*="BẮT ĐẦU"]:hover {
        background-color: #60a5fa;
        border-color: #93c5fd;
    }
    QPushButton[text*="BẮT ĐẦU"]:pressed {
        background-color: #2563eb;
        border-color: #3b82f6;
    }

    /* Danger Button - Đỏ dịu hơn */
    QPushButton[text*="Dừng"] {
        background-color: #b91c1c;
        border: 1px solid #dc2626;
        color: #ffffff;
    }
    QPushButton[text*="Dừng"]:hover {
        background-color: #dc2626;
        border-color: #ef4444;
    }
    
    /* ========== Table ========== */
    QTableWidget {
        background-color: #000000;
        gridline-color: #333333;
        border: 1px solid #333333;
        border-radius: 10px;
        selection-background-color: rgba(100, 100, 100, 0.2);
        selection-color: #ffffff;
        alternate-background-color: #0a0a0f;
    }
    QTableWidget::item {
        padding: 8px;
        border: none;
    }
    QTableWidget::item:selected {
        background-color: rgba(100, 100, 100, 0.3);
        color: #ffffff;
    }
    QTableWidget::item:hover {
        background-color: rgba(100, 100, 100, 0.15);
    }
    QHeaderView::section {
        background-color: #0f172a;
        color: #cbd5e1;
        padding: 10px 8px;
        border: none;
        border-bottom: 1px solid #333333;
        border-right: 1px solid #333333;
        font-weight: 600;
        font-size: 10pt;
    }
    QHeaderView::section:first {
        border-top-left-radius: 10px;
    }
    QHeaderView::section:last {
        border-top-right-radius: 10px;
        border-right: none;
    }
    QHeaderView::section:hover {
        background-color: #1e293b;
    }

    /* ========== Progress Bar ========== */
    QProgressBar {
        border: 1px solid #333333;
        border-radius: 8px;
        text-align: center;
        background-color: #0a0a0f;
        color: #cbd5e1;
        padding: 3px;
        font-weight: 500;
        font-size: 9.5pt;
        height: 24px;
    }
    QProgressBar::chunk {
        background-color: #555555;
        border-radius: 6px;
    }
    
    /* Progress Bar trong GroupBox */
    QGroupBox QProgressBar {
        height: 32px;
        font-size: 10pt;
        font-weight: 600;
    }
    QGroupBox QProgressBar::chunk {
        background-color: #555555;
    }

    /* ========== Status Bar ========== */
    QLabel#StatusBar {
        color: #cbd5e1;
        padding: 8px 12px;
        background-color: #000000;
        border-top: 1px solid #333333;
        border-radius: 0px;
        font-size: 10pt;
    }

    /* ========== Scrollbar ========== */
    QScrollBar:vertical {
        background-color: #000000;
        width: 12px;
        border: none;
        border-radius: 6px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background-color: #333333;
        border-radius: 6px;
        min-height: 30px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #555555;
    }
    QScrollBar::handle:vertical:pressed {
        background-color: #222222;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background-color: #000000;
        height: 12px;
        border: none;
        border-radius: 6px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background-color: #333333;
        border-radius: 6px;
        min-width: 30px;
        margin: 2px;
    }
    QScrollBar::handle:horizontal:hover {
        background-color: #555555;
    }
    QScrollBar::handle:horizontal:pressed {
        background-color: #222222;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    /* ========== Tooltip ========== */
    QToolTip {
        background-color: #0f172a;
        color: #cbd5e1;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 9.5pt;
    }
"""

# ======================================
# BOOT
# ======================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
    