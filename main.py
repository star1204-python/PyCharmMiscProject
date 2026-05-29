import os
import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# 使用官方推薦最新的獨立套件，移除舊版 langchain-community 的 sunset 警告
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# 1. 初始化 FastAPI 應用
app = FastAPI(
    title="Enterprise RAG Local Backend",
    description="地端完全免費的 RAG 企業級知識庫系統 (Windows 穩定版)",
    version="2.2.0"
)

# 2. 定義儲存路徑與初始化 Ollama 向量/LLM 模型
PERSIST_DIRECTORY = "./chroma_db"
embeddings = OllamaEmbeddings(model="llama3")
local_llm = ChatOllama(model="llama3", temperature=0.2)

# 初始化 Chroma 向量資料庫連線
vector_store = Chroma(
    persist_directory=PERSIST_DIRECTORY,
    embedding_function=embeddings
)


# 3. 定義 API 請求與回應結構 (符合 Pydantic V2 規範)
class ChatRequest(BaseModel):
    user_question: str = Field(
        ...,
        description="用戶想要詢問 AI 的問題",
        json_schema_extra={"example": "請問公司的新進同仁有幾天特休？"}
    )


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = Field(description="AI 參考的原始文本段落來源")


# 4. 建立 RAG 專用的提示詞範本
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
     "你是一個專業的企業知識庫助手。請嚴格根據下方從公司資料庫檢索出來的「參考內容」來回答用戶問題。如果資料中沒有提到相關資訊，請老實回答『抱歉，在公司目前的文檔中找不到相關解答』，絕對不能憑空捏造。\n\n【參考內容】：\n{context}"),
    ("user", "{user_question}")
])


# 5. [接口一] 上傳 PDF 文件並建立索引 (安全暫存版：徹底解決 Windows 檔案鎖死與權限問題)
@app.post("/api/v1/upload", summary="上傳企業 PDF 知識庫文件")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="目前僅支援上傳 .pdf 格式檔案")

    # 定義一個臨時儲存的實體路徑
    temp_file_path = f"temp_{file.filename}"

    try:
        # 步驟 A: 先將前端傳來的二進位檔案寫入本地磁碟，避免記憶體讀取權限衝突
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # 步驟 B: 從實體路徑安全讀取並解析 PDF 文字
        pdf_reader = PdfReader(temp_file_path)
        raw_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                raw_text += text + "\n"

        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="PDF 檔案內容為空或無法解析文字")

        # 步驟 C: 使用 LangChain 文字切碎器，將長文章切成 500 字的小區塊 (Chunks)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len
        )
        chunks = text_splitter.split_text(raw_text)

        # 步驟 D: 非同步將切碎的文字與來源標籤轉為向量，存入最新版 Chroma 向量資料庫
        # 使用 asyncio.to_thread 確保密集的 Embedding 計算不卡死 FastAPI 主事件迴圈
        await asyncio.to_thread(
            vector_store.add_texts,
            texts=chunks,
            metadatas=[{"source": file.filename} for _ in chunks]
        )

        return {"message": f"成功解析並匯入檔案：{file.filename}，共生成 {len(chunks)} 個知識片段。"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檔案處理失敗: {str(e)}")

    finally:
        # 步驟 E: 無論成功或失敗，最後都把臨時檔案刪除，確保專案目錄乾淨
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass


# 6. [接口二] 自動檢索並對話 (RAG Pipeline)
@app.post("/api/v1/chat", response_model=ChatResponse, summary="自動檢索知識庫並回答問題")
async def rag_chat(request: ChatRequest):
    try:
        # 步驟 A: 將用戶問題拿去 ChromaDB 做語意相似度檢索，自動撈出最相關的前 3 筆文本段落
        docs = await asyncio.to_thread(
            vector_store.similarity_search,
            query=request.user_question,
            k=3
        )

        # 步驟 B: 提取檢索出來的內容與原始來源檔名
        retrieved_context = "\n---\n".join([doc.page_content for doc in docs])
        sources = [doc.metadata.get("source", "未知來源") for doc in docs]

        # 如果資料庫是完全空的，提醒用戶先上傳
        if not retrieved_context.strip():
            return ChatResponse(answer="抱歉，目前本地知識庫中沒有任何資料，請先透過上傳接口提供 PDF 文件。", sources=[])

        # 步驟 C: 組裝 LangChain LLM 鏈 (LCEL 語法)
        chain = prompt_template | local_llm | StrOutputParser()

        # 步驟 D: 呼叫地端 Ollama 進行推理生成
        ai_answer = await asyncio.to_thread(
            chain.invoke,
            {"context": retrieved_context, "user_question": request.user_question}
        )

        return ChatResponse(answer=ai_answer, sources=list(set(sources)))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG 檢索生成失敗: {str(e)}")


# 7. 啟動邏輯
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

