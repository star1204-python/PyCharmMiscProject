# 🏢 Local Enterprise RAG Knowledge Base System

基於 Python FastAPI 與 LangChain 框架打造的地端完全免費、高隱私企業級知識庫（RAG）問答系統 [1]。本專案完全整合本地開源模型（Ollama / Llama 3）與向量資料庫（ChromaDB），實現無須外部 API Key、無資料外洩風險的智慧文檔檢索與生成服務。

## 🌟 專案核心亮點與後端設計
* **地端去識別化隱私架構**：整合本地 Ollama (Llama 3)，確保企業機密 PDF 文件完全留在本地，杜絕資料上雲外洩。
* **高併發非同步優化**：利用 FastAPI 的 `asyncio` 搭配 `asyncio.to_thread`，將計算密集型（Embedding、LLM 推理）任務移至獨立執行緒，保障後端主事件迴圈（Event Loop）不卡死。
* **反胡言亂語機制（Anti-Hallucination）**：透過 Prompt Engineering 設計嚴格比對機制。當檢索的 Context 未包含答案時，系統老實回覆「不知道」，避免 AI 憑空捏造。
* **產業標準架構**：採用 Pydantic V2 進行前端資料驗證、RESTful API 路由設計，並內建 Windows 環境下高穩定的實體檔案安全暫存機制。

## 🛠️ 技術棧 (Tech Stack)
* **後端框架**：FastAPI (Python)
* **AI 框架**：LangChain, LangChain-Chroma
* **本地模型群**：Ollama (Llama 3), Nomic-Embed-Text (向量嵌入)
* **資料庫**：ChromaDB (本地向量資料庫)
* **文件解析**：PyPDF (PDF 文字提取)
* **網頁伺服器**：Uvicorn (ASGI)

## 📂 專案檔案結構 (Repository Structure)
```text
.
├── main.py              # FastAPI 核心邏輯與 RAG 管道
├── requirements.txt     # 專案套件依賴清單
└── README.md            # 專案說明書
```

## 🚀 快速開始 (Quick Start)

### 1. 本地環境準備
請確保您的電腦已安裝並啟動了 [Ollama](https://ollama.com)。
並在終端機拉取推理模型與向量嵌入模型：
```bash
ollama pull llama3
ollama pull nomic-embed-text
```

### 2. 建立虛擬環境與安裝套件
```bash
# 建立虛擬環境
python -m venv .venv

# 啟用虛擬環境 (Windows)
.venv\Scripts\activate

# 安裝所有相依套件
pip install -r requirements.txt
```

### 3. 啟動後端服務
```bash
uvicorn main:app --reload
```
啟動成功後，訪問網頁：[http://localhost:8000/docs](http://localhost:8000/docs) 進入 Swagger UI 自動化 API 文件面板。

## 🧪 測試工作流 (Workflow)

### Step 1: 知識庫資料餵食 (`POST /api/v1/upload`)
* 在 Swagger 介面點擊 `Try it out`。
* 上傳企業手冊或法規之 PDF 檔案。
* 系統將自動進行 **PDF 文字解析 ➔ 500字智能切碎 ➔ 向量化 (Embedding) ➔ 存入 ChromaDB**。

### Step 2: 自動語意檢索對話 (`POST /api/v1/chat`)
* 用戶僅需傳入問題：`{ "user_question": "請問員工福利有提到電腦補助嗎？" }`。
* 後端管線會先去 ChromaDB 進行相似度比對，自動提取最相關的前 3 筆段落，組裝為 Context 送給 Llama 3 進行語意分析與回答。
