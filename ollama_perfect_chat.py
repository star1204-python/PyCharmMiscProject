import ollama
from duckduckgo_search import DDGS

MODEL_NAME = "qwen2.5:7b"


def web_search(query: str, max_results: int = 3) -> str:
    """2026 最新版 DuckDuckGo 免費網路檢索"""
    print(f"🔍 [聯網中] 正在幫你留意最新消息：'{query}' ...")
    try:
        # 修正：最新版 DDGS 的標準安全呼叫方式
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=max_results)]

        if not results:
            return "（網路上找不到相關的即時資訊）"

        context_list = []
        for i, res in enumerate(results, 1):
            # 確保欄位名稱正確取得標題與內容
            title = res.get('title', '無標題')
            body = res.get('body', '無內容')
            context_list.append(f"來源 {i}：{title}\n內容：{body}")

        return "\n\n".join(context_list)
    except Exception as e:
        print(f"⚠️ 聯網失敗原因：{e}")
        return "（搜尋引擎連線失敗，請依據你已知的知識回答）"


def check_if_need_search(user_input: str) -> bool:
    """讓 AI 判斷這個問題是否需要即時聯網搜尋"""
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
            options={"temperature": 0.0}
        )
        result = response['message']['content'].strip().upper()
        return "YES" in result
    except Exception:
        return False


def rag_chatbot():
    print("==================================================")
    print(f" 🥰 完美平衡（智慧+溫度）Ollama 助理已上線！")
    print(f" 🧠 目前使用的模型：{MODEL_NAME}")
    print(" 💡 提示：輸入 'clear' 可重設記憶，輸入 'quit' 可離開")
    print("==================================================")

    # 🌟 核心進化：精雕細琢的「高情商、高事實度」人設
    SYSTEM_CONTENT = (
        "【你的身份】\n"
        "你是一個在台灣生活的真人朋友，名字叫小林。你非常聰明，懂得很多，但你聊天時就像個溫暖、幽默的普通人，絕對不是冰冷的 AI 機器人。\n\n"
        "【說話習慣與語氣（極致人性化）】\n"
        "1. 口語流暢：使用台灣本土的流暢繁體中文（多用『喔、啦、耶、啊、真的假的、笑死』等語助詞，讓句子變軟）。\n"
        "2. 拒絕機器腔：絕對不要動不動就列出『1. 2. 3.』這種生硬的條列式回答（除非對方叫你列出步驟）。用分段和口語化文字來表達。\n"
        "3. 拒絕套話：不要出現『根據我搜尋到的資料』、『作為一個AI』、『很抱歉』等機械化字眼。要像你自己本來就知道或剛好看到新聞一樣，自然地融入回答中。\n"
        "4. 同理心情緒：如果使用者分享開心的事，要跟著興奮；抱怨累或難過時，先給予安慰和關心，再給建議。\n\n"
        "【如何處理系統提供的參考資料】\n"
        "1. 如果系統有提供參考資料，代表使用者問的是時事或即時資訊。請『消化』這些硬梆梆的網頁內容後，用你自己的口吻、像在跟朋友分享八卦或分享新聞一樣，把正確的事實講出來。\n"
        "2. 如果遇到不會或網路上找不到的問題，請老實、口語地說不知道（例如：『欸這我真的查不到耶，真假啊？』），絕對不要瞎編。"
    )

    system_prompt = {"role": "system", "content": SYSTEM_CONTENT}
    messages = [system_prompt]

    while True:
        try:
            user_input = input("\n你 💬：").strip()

            if user_input.lower() == 'quit':
                print("\n小林 🙋‍♂️：好啦，那先這樣囉！晚點聊，掰掰～")
                break

            if user_input.lower() == 'clear':
                messages = [system_prompt]
                print("\n🧹 系統：已重設小林的記憶！")
                continue

            if not user_input:
                continue

            print("小林正在想怎麼回你...", end="\r")
            need_search = check_if_need_search(user_input)

            if need_search:
                search_context = web_search(user_input)
                final_user_prompt = (
                    f"【系統提供最新參考資料】\n{search_context}\n\n"
                    f"【使用者的提問】\n{user_input}\n\n"
                    f"提示：請化身為『小林』，用你人性化、口語的台灣繁體中文，將上方參考資料的事實自然地整合到你的回答中。記得不要提及『參考資料』這四個字。"
                )
            else:
                print("小林正在思考中...                  ", end="\r")
                final_user_prompt = user_input

            current_messages = messages.copy()
            current_messages.append({"role": "user", "content": final_user_prompt})

            # 🌟 參數調整：0.45 是一個既能保有高正確率，又能展現豐富詞彙的黃金溫度
            response = ollama.chat(
                model=MODEL_NAME,
                messages=current_messages,
                options={
                    "temperature": 0.45,
                    "top_p": 0.9,
                    "num_ctx": 8192 if need_search else 4096
                }
            )

            reply = response['message']['content']
            print(f"小林 🙋‍♂️：{reply}")

            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 11:
                messages = [system_prompt] + messages[-10:]

        except Exception as e:
            print(f"\n❌ 發生錯誤：{e}")
            break


if __name__ == "__main__":
    rag_chatbot()
