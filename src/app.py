import os
import time
import random
import datetime
import urllib.request
import urllib.error
# pyrefly: ignore [missing-import]
from flask import Flask, jsonify, render_template, request

# Import psutil optionally to get real system statistics if available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

app = Flask(__name__)

# Track start time for uptime calculation
START_TIME = time.time()

# Mock logs generation
LOG_MESSAGES = [
    ("INFO", "auth-service", "使用者身分驗證成功，用戶 UID 98213。"),
    ("INFO", "api-gateway", "GET /api/v1/status - 200 OK (回傳耗時 12ms)"),
    ("WARNING", "db-pool", "資料庫連線池大小接近臨界值 (目前作用中: 18/20)。"),
    ("INFO", "payment-api", "接收到來自支付處理商 Stripe 的 Webhook：payment_intent.succeeded。"),
    ("ERROR", "cache-redis", "Redis 連線逾時。正在嘗試重新連線 (1/3)..."),
    ("INFO", "cache-redis", "成功重新建立與 Redis 快取主節點的連線。"),
    ("WARNING", "storage-service", "儲存分割區 /data 空間使用率已超過 80%。"),
    ("ERROR", "auth-service", "使用者 'admin' 登入失敗，來源 IP 192.168.1.100。"),
    ("INFO", "nginx-ingress", "IP 203.0.113.195 - SSL 握手完成，使用 TLSv1.3"),
    ("WARNING", "scheduler", "排程工作 'cleanup_temp_files' 延遲執行達 45 秒。"),
    ("INFO", "search-indexer", "成功建立 1,245 份文件的搜尋索引，耗時 1.4 秒。")
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/metrics")
def get_metrics():
    # Calculate uptime
    uptime_seconds = int(time.time() - START_TIME)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

    if HAS_PSUTIL:
        # Real statistics
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        # Mock network values that look reasonable but base on system IO if possible
        net_io = psutil.net_io_counters()
        # Scale to KB/s for display
        net_in = round((net_io.bytes_recv % 5000000) / 1024.0, 1)
        net_out = round((net_io.bytes_sent % 5000000) / 1024.0, 1)
    else:
        # Mock statistics with realistic fluctuations
        cpu = round(30.0 + random.uniform(-15.0, 15.0), 1)
        # Keep CPU bounds safe
        cpu = max(5.0, min(98.0, cpu))
        
        # Memory fluctuates slowly
        memory = round(64.5 + random.uniform(-2.0, 2.0), 1)
        
        # Disk changes very slowly
        disk = 45.8
        
        # Network speeds in KB/s
        net_in = round(120.0 + random.uniform(-80.0, 150.0), 1)
        net_out = round(85.0 + random.uniform(-50.0, 100.0), 1)

    latency = round(15.0 + random.uniform(-10.0, 30.0), 1)
    latency = max(5.0, latency)

    return jsonify({
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "network_in": net_in,
        "network_out": net_out,
        "latency": latency,
        "uptime": uptime_str,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    })

@app.route("/api/ping")
def ping_service():
    url = request.args.get("url", "https://www.google.com")
    
    # Simple URL sanity normalization
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    start_time = time.time()
    try:
        # Use urllib to request the site with a 5-second timeout
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Flask-SRE-Monitor/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            status = "UP" if status_code < 400 else "DOWN"
    except urllib.error.HTTPError as e:
        status_code = e.code
        status = "DOWN"
    except urllib.error.URLError:
        status_code = 0
        status = "DOWN"
    except Exception:
        status_code = -1
        status = "DOWN"

    latency = round((time.time() - start_time) * 1000, 1)

    return jsonify({
        "url": url,
        "status": status,
        "status_code": status_code,
        "latency": latency if status_code > 0 else 0,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/logs")
def get_logs():
    level_filter = request.args.get("level", "ALL").upper()
    limit = int(request.args.get("limit", 20))

    # Generate dynamic log entries with timestamps relative to now
    now = datetime.datetime.now()
    generated_logs = []

    # Seed logs with decreasing seconds from current time
    attempts = 0
    max_attempts = 500
    while len(generated_logs) < limit and attempts < max_attempts:
        log_time = now - datetime.timedelta(seconds=attempts * random.randint(3, 15))
        level, service, message = random.choice(LOG_MESSAGES)
        
        if level_filter == "ALL" or level == level_filter:
            generated_logs.append({
                "timestamp": log_time.strftime("%H:%M:%S"),
                "level": level,
                "service": service,
                "message": message
            })
        attempts += 1
            
    # Sort chronological (oldest first or newest first, let's do newest first for dashboard)
    return jsonify(generated_logs)

# In-memory Stocks Database
STOCKS_DATA = {
    "GOOGL": {"name": "Alphabet Inc.", "price": 175.50, "prev_close": 174.20, "history": [174.20, 174.50, 174.80, 175.10, 175.50]},
    "MSFT": {"name": "Microsoft Corp.", "price": 420.20, "prev_close": 422.00, "history": [422.00, 421.50, 421.00, 420.50, 420.20]},
    "AAPL": {"name": "Apple Inc.", "price": 180.80, "prev_close": 179.50, "history": [179.50, 179.80, 180.00, 180.50, 180.80]},
    "AMZN": {"name": "Amazon.com Inc.", "price": 185.10, "prev_close": 184.00, "history": [184.00, 184.20, 184.50, 184.80, 185.10]},
    "SRE-CLOUD": {"name": "SRE Cloud Systems Index", "price": 100.00, "prev_close": 98.50, "history": [98.50, 99.00, 99.20, 99.70, 100.00]}
}

# In-memory Company Incidents & Shifts
COMPANY_DATA = {
    "shifts": [
        {"shift": "早班 (08:00 - 16:00)", "name": "陳大同 (Alice Chen)", "assignment": "東京叢集 A"},
        {"shift": "中班 (16:00 - 24:00)", "name": "林小明 (Bob Smith)", "assignment": "俄勒岡叢集 B"},
        {"shift": "晚班 (00:00 - 08:00)", "name": "張華強 (Charlie Day)", "assignment": "都柏林叢集 C"}
    ],
    "incidents": [
        {"id": "INC-104", "title": "Redis 記憶體碎片率超出閾值", "status": "INVESTIGATING", "assignee": "陳大同 (Alice Chen)", "time": "09:42"},
        {"id": "INC-105", "title": "CDN 源站防護延遲異常", "status": "PENDING", "assignee": "林小明 (Bob Smith)", "time": "10:15"},
        {"id": "INC-106", "title": "自動擴容冷卻時間逾時", "status": "RESOLVED", "assignee": "張華強 (Charlie Day)", "time": "08:10"}
    ]
}

@app.route("/api/stocks")
def get_stocks():
    global STOCKS_DATA
    response_data = []
    for ticker, stock in STOCKS_DATA.items():
        # Fluctuates price slightly
        change_pct = random.uniform(-0.005, 0.005)
        stock["price"] = round(stock["price"] * (1 + change_pct), 2)
        
        # Append to history
        stock["history"].append(stock["price"])
        if len(stock["history"]) > 10:
            stock["history"].pop(0)
            
        # Calculate changes
        diff = round(stock["price"] - stock["prev_close"], 2)
        pct = round((diff / stock["prev_close"]) * 100, 2)
        
        response_data.append({
            "ticker": ticker,
            "name": stock["name"],
            "price": stock["price"],
            "prev_close": stock["prev_close"],
            "change": diff,
            "change_percent": pct,
            "history": stock["history"]
        })
    return jsonify(response_data)

@app.route("/api/company", methods=["GET"])
def get_company():
    return jsonify(COMPANY_DATA)

@app.route("/api/company/action", methods=["POST"])
def post_company_action():
    # Support json and form parameters
    if request.is_json:
        data = request.get_json() or {}
        action = data.get("action")
    else:
        action = request.form.get("action")

    if not action:
        return jsonify({"error": "Missing action parameter"}), 400

    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    logs = []

    if action == "restart_service":
        logs = [
            f"[{now_str}] [INFO] 正在連線至 redis-cluster-master 快取叢集...",
            f"[{now_str}] [INFO] 發送 SIGTERM 信號關閉進程 pid 4920...",
            f"[{now_str}] [WARNING] Redis 快取服務已安全關閉。",
            f"[{now_str}] [INFO] 重新啟動 redis-server 守護程序 (載入設定: /etc/redis.conf)...",
            f"[{now_str}] [INFO] Redis 伺服器已重新上線，成功恢復用戶端連接。"
        ]
        # Resolve INC-104 since they restarted Redis
        for inc in COMPANY_DATA["incidents"]:
            if inc["id"] == "INC-104":
                inc["status"] = "RESOLVED"
    elif action == "scale_pods":
        logs = [
            f"[{now_str}] [INFO] 載入 Kubernetes 部署設定檔: ingress-api-deployment...",
            f"[{now_str}] [INFO] 開始擴容 replicas 副本數：3 -> 10。",
            f"[{now_str}] [INFO] 正在建立並調度 Pods: api-pod-x92, api-pod-k41, api-pod-z12...",
            f"[{now_str}] [INFO] Pods 狀態變更: ContainerCreating (建立中) -> Running (運行中)。",
            f"[{now_str}] [INFO] 健康檢查 (Readiness probe) 通過，已成功更新 Ingress 負載平衡路由規則。"
        ]
    elif action == "flush_cdn":
        logs = [
            f"[{now_str}] [INFO] 正在清除 Cloudflare 邊緣快取 (網域區域: ckc101.sre)...",
            f"[{now_str}] [INFO] 萬用字元路徑 '/*' 清除請求已送至佇列。",
            f"[{now_str}] [INFO] 清除快取指令已成功廣播至全球 284 個邊緣節點 (POPs)。",
            f"[{now_str}] [INFO] 快取清除完成，最新 Cache-Control 已套用。"
        ]
        # Resolve INC-105
        for inc in COMPANY_DATA["incidents"]:
            if inc["id"] == "INC-105":
                inc["status"] = "RESOLVED"
    else:
        return jsonify({"error": f"Unknown action '{action}'"}), 400

    return jsonify({
        "status": "SUCCESS",
        "action": action,
        "logs": logs,
        "incidents": COMPANY_DATA["incidents"]
    })

@app.route('/blog')
def blog_home():
    # 這裡定義你的 Google 文件 ID
    google_doc_id = "e/2PACX-1vSZIDp4jBIGPZzwmL473aMjP25nRiPyMZE7U_62KXH8jB6MiSCNQrexzjbEOgmhy0KJq0Ll7yd_Mj_v"
    return render_template('blog.html', doc_id=google_doc_id)

@app.route('/aws-guide')
def aws_guide():
    # 這是你提供的文件 ID
    doc_id = "e/2PACX-1vSZIDp4jBIGPZzwmL473aMjP25nRiPyMZE7U_62KXH8jB6MiSCNQrexzjbEOgmhy0KJq0Ll7yd_Mj_v"
    return render_template('post.html', doc_id=doc_id)

@app.route('/github')
def github_preview():
    # Read README.md content to render it in front-end
    readme_content = ""
    if os.path.exists("README.md"):
        try:
            with open("README.md", "r", encoding="utf-8") as f:
                readme_content = f.read()
        except Exception:
            readme_content = "# Error reading README.md"

    # Build the file list
    file_list = []
    for root, dirs, files in os.walk('.'):
        # Exclude directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('venv', '.venv', '__pycache__', 'sre_app_stderr.log')]
        for file in files:
            if not file.startswith('.'):
                file_path = os.path.relpath(os.path.join(root, file), '.')
                file_list.append(file_path)

    # Sort the files alphabetically
    file_list.sort()
    
    return render_template('github.html', files=file_list, readme=readme_content)

if __name__ == "__main__":
    # Ensure templates can auto-reload
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(host="0.0.0.0", port=19191, debug=True)
