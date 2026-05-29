import ollama
from duckduckgo_search import DDGS

MODEL_NAME = "qwen2.5:14b"


def web_search(query: str, max_results: int = 3) -> str:
    """使用 DuckDuckGo 免費搜尋網路"""
    print(f"🔍 [系統偵測需要聯網] 正在上網搜尋：'{query}' ...")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "（網路上找不到相關的即時資訊）"
        context_list = [f"來源 {i}：{res['title']}\n內容：{res['body']}" for i, res in enumerate(results, 1)]
        return "\n\n".join(context_list)
    except Exception as e:
        return f"（搜尋引擎連線失敗：{e}）"


def check_if_need_search(user_input: str) -> bool:
    """🌟 讓 AI 判斷這個問題是否需要即時聯網搜尋"""
    # 建立一個極簡的判斷 Prompt，限制 AI 只能回答 YES 或 NO
    judgment_prompt = (
        "你是一個判斷器。請分析使用者的輸入，評估是否需要『即時聯網搜尋』才能精準回答。\n"
        "需要搜尋的情況：詢問天氣、最新新聞、時事、近期活動、特定人物的近況、最新科技、股票價格、或是本機模型不可能知道的即時資料。\n"
        "不需要搜尋的情況：日常打招呼、閒聊、分享心情、詢問數學或程式碼邏輯、單純的文字創作或翻譯。\n\n"
        f"使用者輸入：『{user_input}』\n\n"
        "請嚴格只回傳大寫的 'YES' 或 'NO'，絕對不要包含任何其他字元或標點符號。"
    )

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": judgment_prompt}],
            options={"temperature": 0.0}  # 溫度設為 0，確保判斷高度穩定
        )
        result = response['message']['content'].strip().upper()
        # 只要包含 YES 就代表需要搜尋
        return "YES" in result
    except Exception:
        return False  # 發生錯誤時預設不搜尋，走一般對話


def rag_chatbot():
    print("==================================================")
    print(f" 🧠 智能決策聯網 Ollama 助理已上線！")
    print(f" 🧠 目前使用的模型：{MODEL_NAME}")
    print(" 💡 提示：AI 會自己決定要不要上網，不再盲目搜尋囉！")
    print("==================================================")

    SYSTEM_CONTENT = (
        "你是一個專業且具備智慧聯網能力的繁體中文助理。\n"
        "如果系統有提供『參考資料』，請結合該資料來回答；如果沒有提供，代表這是日常閒聊或邏輯問題，請直接用你所學的知識回答。\n"
        "回答一律使用繁體中文，保持自然流暢，不要提及『根據參考資料』等機械化字眼。"
    )

    system_prompt = {"role": "system", "content": SYSTEM_CONTENT}
    messages = [system_prompt]

    while True:
        try:
            user_input = input("\n你 💬：").strip()

            if user_input.lower() == 'quit':
                print("\n助理 🤖：再見！")
                break

            if user_input.lower() == 'clear':
                messages = [system_prompt]
                print("\n🧹 系統：已重設助理的記憶！")
                continue

            if not user_input:
                continue

            # 🌟 核心優化：先讓 AI 判斷要不要上網
            print("助理正在分析問題意圖...", end="\r")
            need_search = check_if_need_search(user_input)

            if need_search:
                # 需要搜尋：抓取網路資料並包裝
                search_context = web_search(user_input)
                final_user_prompt = (
                    f"【參考資料】\n{search_context}\n\n"
                    f"【使用者問題】\n{user_input}\n\n"
                    f"請結合上方的即時參考資料，準確回答使用者的問題。"
                )
            else:
                # 不需要搜尋：直接使用原本的問題
                print("🧠 [日常對話/邏輯思考] 本機處理中...          ", end="\r")
                final_user_prompt = user_input

            # 複製當前記憶並加入本次的輸入
            current_messages = messages.copy()
            current_messages.append({"role": "user", "content": final_user_prompt})

            # 呼叫 Ollama 生成最終回答
            response = ollama.chat(
                model=MODEL_NAME,
                messages=current_messages,
                options={
                    "temperature": 0.3,
                    "num_ctx": 8192 if need_search else 4096  # 根據有沒有搜尋動態調整上下文大小，省記憶體
                }
            )

            reply = response['message']['content']
            print(f"助理 🤖：{reply}")

            # 保持記憶乾淨：只存使用者的「純問題」與 AI 的「純回答」
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 11:
                messages = [system_prompt] + messages[-10:]

        except Exception as e:
            print(f"\n❌ 發生錯誤：{e}")
            break


if __name__ == "__main__":
    rag_chatbot()
