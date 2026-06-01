import os
import asyncio
from typing import List
import datetime
import traceback  # 引入錯誤軌跡追蹤工具
from fastapi import FastAPI, HTTPException, UploadFile, File, Header
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# 引入符合 SQLAlchemy 最新標準的套件
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from rank_bm25 import BM25Okapi

# =====================================================================
# 1. 系統初始化與資料庫設定 (對話紀錄持久化)
# =====================================================================
app = FastAPI(
    title="Enterprise Ultimate RAG System",
    description="旗艦級地端 RAG 知識庫系統（內建混合檢索與長期記憶體）",
    version="3.1.0"
)

# 使用 SQLAlchemy 初始化本地資料庫
DATABASE_URL = "sqlite:///./chat_history.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 使用最新指定之 ORM 宣告路徑，移除過時警告
Base = declarative_base()


# 定義對話紀錄資料表模型 (ORM)
class ChatMessageModel(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, comment="辨識不同對話視窗的 ID")
    role = Column(String, comment="user 或 assistant")
    content = Column(Text, comment="對話內容")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# 自動建立資料庫與資料表檔案 (chat_history.db)
Base.metadata.create_all(bind=engine)

# =====================================================================
# 2. AI 模型與全域變數設定
# =====================================================================
PERSIST_DIRECTORY = "./chroma_db"
embeddings = OllamaEmbeddings(model="nomic-embed-text")  # 使用高相容性輕量向量模型
local_llm = ChatOllama(model="llama3", temperature=0.2)

vector_store = Chroma(
    persist_directory=PERSIST_DIRECTORY,
    embedding_function=embeddings
)

# 用於 BM25 關鍵字搜尋的全域記憶體暫存
bm25_corpus: List[str] = []
bm25_instance: BM25Okapi = None


# =====================================================================
# 3. Pydantic 資料結構定義 (符合 Pydantic V2 規範)
# =====================================================================
class ChatRequest(BaseModel):
    user_question: str = Field(
        ...,
        description="用戶輸入的問題",
        json_schema_extra={"example": "那我應該提早多久請假？"}
    )


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = Field(description="AI 參考的原始文件來源")
    history_used: int = Field(description="本次對話參考的前置歷史訊息輪數")


# =====================================================================
# 4. 旗艦版 RAG 提示詞範本 (動態融入歷史記憶與參考內容)
# =====================================================================
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
     "你是一個具備長期對話記憶的企業級智慧助理。請嚴格根據下方提供的「參考內容」來回答用戶的問題。如果資料中沒有提到相關資訊，請老實回答『抱歉，在公司目前的文檔中找不到相關解答』，絕對不能憑空捏造。\n\n【參考內容】：\n{context}\n\n【前情提要（歷史對話紀錄）】：\n{chat_history}"),
    ("user", "{user_question}")
])


# =====================================================================
# 5. [接口一] 上傳 PDF 文件並同步更新 BM25 索引 (Windows 強化除蟲版)
# =====================================================================
@app.post("/api/v1/upload", summary="上傳 PDF 檔案並建立混合檢索索引")
async def upload_document(file: UploadFile = File(...)):
    global bm25_corpus, bm25_instance
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="目前僅支援上傳 .pdf 格式檔案")

    temp_file_path = f"temp_{file.filename}"
    try:
        # A. 安全寫入本地實體檔案，防止記憶體鎖死
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # B. 以 UTF-8 標準安全讀取並解析 PDF 文字
        pdf_reader = PdfReader(temp_file_path)
        raw_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                # 強制轉換為 utf-8 乾淨字串，防止 Windows cp950 編碼出錯
                raw_text += text.encode('utf-8', errors='ignore').decode('utf-8') + "\n"

        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="PDF 檔案內容為空或無法解析文字")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_text(raw_text)

        # C. 寫入語意向量資料庫 (ChromaDB)
        await asyncio.to_thread(
            vector_store.add_texts,
            texts=chunks,
            metadatas=[{"source": file.filename} for _ in chunks]
        )

        # D. 安全同步更新關鍵字資料庫 (BM25)，加入防空值校正
        cleaned_chunks = [c.strip() for c in chunks if c.strip()]
        bm25_corpus.extend(cleaned_chunks)

        # 進行分詞優化
        tokenized_corpus = [doc.replace("\n", " ").split() for doc in bm25_corpus]

        if tokenized_corpus:
            bm25_instance = BM25Okapi(tokenized_corpus)

        return {"message": f"成功匯入：{file.filename}，已啟動向量與關鍵字雙索引混合檢索管線。"}

    except Exception as e:
        # 🌟 終極大絕招：捕捉完整的紅色噴錯軌跡，同時印在 PyCharm 並直接回傳給網頁前端
        error_details = traceback.format_exc()
        print("======== [後端內部崩潰詳細軌跡] ========\n", error_details)
        raise HTTPException(
            status_code=500,
            detail=f"地端 RAG 執行崩潰！錯誤原因: {str(e)}\n\n詳細除錯路徑:\n{error_details}"
        )
    finally:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass


# =====================================================================
# 6. [接口二] 混合檢索 + 歷史對話持久化管道
# =====================================================================
@app.post("/api/v1/chat", response_model=ChatResponse, summary="混合檢索與多輪對話智慧問答")
async def advanced_rag_chat(
        request: ChatRequest,
        x_session_id: str = Header(default="default-session",
                                   description="對話視窗 ID，用來區分與讀取不同使用者的記憶體")
):
    db = SessionLocal()
    try:
        # 🌟 亮點一：從持久化資料庫中撈出該 Session 最近 4 筆對話紀錄做為歷史上下文
        history_records = db.query(ChatMessageModel) \
            .filter(ChatMessageModel.session_id == x_session_id) \
            .order_by(ChatMessageModel.created_at.desc()) \
            .limit(4).all()

        # 將對話由舊到新排序並格式化
        history_records.reverse()
        formatted_history = ""
        for msg in history_records:
            formatted_history += f"{msg.role.upper()}: {msg.content}\n"

        # 🌟 亮點二：實作混合檢索 (Hybrid Search)
        # 模組 A: 密集向量語意搜尋 (撈出前 2 筆)
        vector_docs = await asyncio.to_thread(vector_store.similarity_search, query=request.user_question, k=2)
        vector_results = [doc.page_content for doc in vector_docs]
        sources = [doc.metadata.get("source", "未知來源") for doc in vector_docs]

        # 模組 B: 稀疏關鍵字搜尋 (BM25) (精準撈出 1 筆關鍵字匹配)
        bm25_results = []
        if bm25_instance is not None:
            tokenized_query = request.user_question.split(" ")
            bm25_docs = bm25_instance.get_top_n(tokenized_query, bm25_corpus, n=1)
            bm25_results = bm25_docs

        # 去重複融合 (De-duplication)
        combined_context_list = list(set(vector_results + bm25_results))
        final_context = "\n---\n".join(combined_context_list)

        if not final_context.strip():
            return ChatResponse(answer="本地知識庫尚未初始化，請先上傳 PDF 文件。", sources=[], history_used=0)

        # 🌟 亮點三：將檢索內容與長期對話記憶塞入 Prompt，呼叫本地 LLM 推理
        chain = prompt_template | local_llm | StrOutputParser()
        ai_answer = await asyncio.to_thread(
            chain.invoke,
            {
                "context": final_context,
                "chat_history": formatted_history if formatted_history else "尚無歷史對話紀錄。",
                "user_question": request.user_question
            }
        )

        # 🌟 亮點四：將本次對話安全地追加記錄至資料庫
        user_msg = ChatMessageModel(session_id=x_session_id, role="user", content=request.user_question)
        ai_msg = ChatMessageModel(session_id=x_session_id, role="assistant", content=ai_answer)
        db.add(user_msg)
        db.add(ai_msg)
        db.commit()

        return ChatResponse(
            answer=ai_answer,
            sources=list(set(sources)),
            history_used=len(history_records)
        )

    except Exception as e:
        db.rollback()
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"對話管線崩潰！錯誤原因: {str(e)}\n\n詳細除錯路徑:\n{error_details}"
        )
    finally:
        db.close()


# 7. 啟動邏輯
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
