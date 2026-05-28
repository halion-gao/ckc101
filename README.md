# SRE 即時運維指揮中心儀表板 (SRE Operations Dashboard)

![Python Testing](https://github.com/halion-gao/ckc101/actions/workflows/python-tests.yml/badge.svg)

本專案是一個針對 SRE (Site Reliability Engineering) 團隊設計的高效能即時運維指揮中心儀表板。基於 **Flask (Backend)** 與 **Vanilla CSS/JS (Frontend)** 構建，具備輕量化的系統監控、診斷工具、動態日誌流分析、即時股市看盤，以及內部知識庫整合功能。

---

## 🌟 核心功能特色

### 1. 🖥️ 運行概覽 (Infrastructure Metrics)
- **實時系統指標**：動態更新 CPU 負載 (Radial Progress)、記憶體使用率、硬碟空間使用率以及網路 I/O 吞吐量 (KB/s)。
- **延遲與負載歷史趨勢**：使用高效能 SVG 折線圖實時繪製延遲與 CPU 變化趨勢。

### 2. 🔌 連線檢測 (Ping Health Checker)
- **服務健康檢測**：輸入 API 端點或網址，驗證可達性、回應狀態碼與連線延遲。
- **檢測歷史紀錄**：表格化記錄近 10 次檢測結果，並配合狀態標籤（正常／異常）進行視覺化警示。

### 3. 📄 即時日誌流 (Real-time Log Terminal)
- **多層級日誌流**：實時輪詢後端產生的系統診斷日誌，支援 `INFO`、`WARNING`、`ERROR` 分級篩選。
- **瀏覽器效能優化 (DOM Limit & GC)**：
  - 限制主控台最大顯示為 **100 條日誌**，當超出限制時自動卸載最舊的 DOM 節點。
  - 同步清理比對快取中對應的唯一鍵 (ID)，避免瀏覽器因長期掛載導致記憶體洩漏與渲染卡頓。

### 4. 📈 晨間股市與午後公司 (Consolidated Ops & Market Ticker)
- **晨間股市監控**：即時更新科技巨頭股價，前端透過 ID 比對進行 **原地更新 (In-place updates)**，徹底消除排版抖動與更新閃爍，並整合 inline SVG 迷你趨勢圖 (Sparklines)。
- **SRE 值班輪替 (Rota) 與故障單管理**：呈現當前值班人員與負責區域，並顯示 Pending／Investigating／Resolved 的故障單。
- **自動化運維面板**：整合自動化復原按鈕（擴容 Pod、重啟快取、清理 CDN 快取），點擊後會以漸進式打字機效果模擬終端指令執行過程。

### 5. 📖 運維文件庫 (Google Doc Integration)
- **嵌入式閱讀**：直接在儀表板中以預覽模式 (`/preview`) 嵌入共用運維規範與故障排除手冊。
- **快速跳轉協作**：提供一鍵跳轉按鈕，在瀏覽器新分頁中開啟 Google 文件的編輯/共用模式。

---

## 🛠️ 技術棧說明
- **後端 (Backend)**: Python, Flask (輕量、原生標準庫相依，確保高效率)
- **前端 (Frontend)**: HTML5, CSS3 (CSS 變數、毛玻璃玻璃擬態 Glassmorphism、暗黑主題)、原生 JavaScript
- **測試 (Testing)**: Pytest (包含 API 端點驗證與 HTML 結構斷言)
- **持續整合 (CI)**: GitHub Actions 工作流自動運行測試

---

## 📂 專案目錄結構
```text
ckc101/
├── src/
│   ├── app.py                # Flask 後端應用程式 (Port 19191)
│   ├── templates/
│   │   └── index.html        # 儀表板 HTML 模板
│   └── static/
│       ├── css/
│       │   └── style.css     # 玻璃擬態與響應式佈局 CSS 樣式
│       └── js/
│           └── main.js       # 輪詢、導覽、原地 DOM 更新、日誌 GC 邏輯
├── test/
│   └── test_app.py           # 整合測試與 API 端點單元測試
├── requirements.txt          # 專案套件相依清單
├── run.sh                    # 開啟服務指令腳本
└── test.sh                   # 執行測試指令腳本
```

---

## 🚀 快速開始

### 1. 環境架設
專案中已包裝 `run.sh` 腳本，會自動在本地建立並啟用虛擬環境 (`.venv`)、安裝相依套件並啟動服務：
```bash
./run.sh
```
若您希望手動操作：
```bash
# 1. 建立虛擬環境
python3 -m venv .venv

# 2. 啟用環境
source .venv/bin/activate

# 3. 安裝套件
pip install -r requirements.txt

# 4. 啟動服務 (預設埠口: 19191)
python src/app.py
```
啟動後在瀏覽器訪問: `http://localhost:19191`

### 2. 執行測試
本專案有著完整的自動化測試。您可以使用以下腳本一鍵執行：
```bash
./test.sh
```
或在虛擬環境啟用狀態下直接運行：
```bash
pytest test/
```
