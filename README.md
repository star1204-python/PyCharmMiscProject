# 🏢 Local Enterprise Ultimate RAG System

基於 Python FastAPI 與 LangChain 框架打造的旗艦級地端全免費、高隱私企業級知識庫（RAG）系統。本專案升級了傳統單一向量搜尋的弊端，自主實作了**「字元級中文混合檢索（Hybrid Search）」**管線，並結合 **SQLAlchemy ORM** 實現了**「多輪對話歷史紀錄持久化」**，具備商業生產環境等級的完整後端架構。

## 🌟 專案核心亮點與後端架構演進

*   **字元級中文混合檢索（Hybrid Search）**：
    針對繁體中文句子無空格之特性，重構檢索管線。整合 `Dense Retrieval`（ChromaDB 密集向量語意搜尋）與 `Sparse Retrieval`（BM25 稀疏關鍵字演算法），並採「中文字元級（Character-level）分詞技術」，大幅改善系統對於特定專有名詞、法規數字、App縮寫（如 AED、1925、DeepSeek）的檢索命中率（Hit Rate）。
*   **非同步對話歷史持久化（Stateful Chat Session）**：
    整合 SQLAlchemy ORM 架構，自動建立關聯式資料庫。將用戶與 AI 的每輪對話軌跡異步持久化存儲，並透過 Header 的 `x-session-id` 實現多使用者記憶隔離（Multi-user Isolation），賦予本地 AI 穩定的長期記憶與上下文推理能力。
*   **PDF 碎裂文字清洗機制（Data Cleaning）**：
    針對複雜排版、多欄位、多圖表的官方文檔（如國防部安全指引手冊），實作自訂文字清洗管線，強制進行 UTF-8 校正並黏合因排版產生的碎裂空格與異常換行，徹底解決 RAG 生產環境中最經典的「PDF 解析地獄」痛點。
*   **高高併發非阻塞設計**：
    針對地端嵌入（Embedding）與本地 LLM 推理等計算密集型（CPU/bound）任務，全面採用 `asyncio.to_thread` 移至獨立線程池（Thread Pool）非同步處理，保障 FastAPI 主事件迴圈（Event Loop）的高吞吐性能。
*   **反胡言亂語機制（Anti-Hallucination）**：
    調降模型溫度（Temperature = 0.0）並重構 Prompt Engineering。限定 AI 僅能優先從檢索到的 Context 提取答案，若文檔未提及則嚴格限制瞎編，回覆「找不到相關解答」。

## 🛠️ 技術棧 (Tech Stack)

*   **後端框架**：FastAPI (Python), Pydantic V2 (資料驗證)
*   **資料庫 ORM**：SQLAlchemy (對話紀錄持久化)
*   **AI 核心框架**：LangChain, LangChain-Chroma
*   **本地模型群**：Ollama (Llama 3 推理模型), Nomic-Embed-Text (向量嵌入)
*   **混合檢索算法**：Rank-BM25 (字元級優化)
*   **文件解析**：PyPDF (PDF 文字提取與清洗)

## 📂 專案檔案結構 (Repository Structure)
```text
.
├── main.py              # 旗艦版 RAG 核心管線 (含混合檢索與持久化)
├── requirements.txt     # 專案套件依賴清單
├── README.md            # 專案說明書
├── chat_history.db      # SQLAlchemy 自動生成的歷史紀錄資料庫 (已進 .gitignore)
└── chroma_db/           # ChromaDB 自動生成的向量數據目錄 (已進 .gitignore)
```

## 🚀 快速開始 (Quick Start)

### 1. 本地環境與模型準備
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

# 一鍵安裝所有旗艦版相依套件
pip install -r requirements.txt
```

### 3. 啟動後端服務
```bash
uvicorn main:app --reload
```
啟動成功後，訪問網頁：[http://localhost:8000/docs](http://localhost:8000/docs) 進入 Swagger UI 自動化 API 文件面板。

## 🧪 測試驗證工作流 (Test Cases)

### Step 1: 匯入高難度多欄 PDF 知識庫 (`POST /api/v1/upload`)
* 上傳《臺灣全民安全指引》PDF 檔案。
* 系統自動啟動 **PDF文字提取 ➔ 碎裂文字黏合清洗 ➔ 250字高密度智能切碎 ➔ 向量與字元級關鍵字雙索引建立**。

### Step 2: 混合檢索與連環問答驗證 (`POST /api/v1/chat`)
* **測試特定專有名詞（Hybrid Search 驗證）**：
  輸入問題：`「中國製App個資蒐集風險」`，系統將精準跨越排版限制，精確抓取並回傳手冊第 12 頁的 `DeepSeek、WeChat、TikTok、小紅書` 等 App 關鍵字。
* **測試長期記憶連環問答（持久化記憶驗證）**：
  在同一個 `x-session-id` 下，第一問：`「安心關懷專線的號碼是多少？」`（AI回覆1925）；第二問：`「那如果遇到核子事故，政府說可以服用什麼片？」`（AI成功接續上下文並回覆碘片）。
