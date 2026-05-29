import os
import re
import ollama
from duckduckgo_search import DDGS

# 🌟 核心修正：切換至 140 億參數的 Qwen 2.5 旗艦中文模型
MODEL_NAME = "qwen2.5:14b"


def clean_web_text(text: str) -> str:
    """清理網頁內文"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    # 🌟 14B 大腦極度強大，我們將限制放寬到 800 字，讓它能閱讀更完整、更有深度的資訊
    return text[:800].strip()


def web_search(query: str, max_results: int = 3) -> str:
    """2026 最新版 DuckDuckGo 安全檢索"""
    print(f"🔍 [聯網中] 正在即時抓取最新網路資料：'{query}' ...")
    try:
        results = []
        with DDGS() as ddgs:
            ddgs_generator = ddgs.text(query, max_results=max_results)
            results = list(ddgs_generator)

        if not results:
            return "（網路暫時沒有查到該事件的即時資訊）"

        context_list = []
        for i, res in enumerate(results, 1):
            title = res.get('title', '無標題')
            body = clean_web_text(res.get('body', ''))
            context_list.append(f"【新聞來源 {i}：{title}】\n詳細內文：{body}")

        print(f"✅ 成功抓取並精煉完成 {len(results)} 筆即時網頁資料！")
        return "\n\n".join(context_list)

    except Exception as e:
        print(f"⚠️ 聯網抓取失敗，原因：{e}")
        return "（搜尋引擎連線失敗，請依據你已知的知識回答）"


def check_if_need_search(user_input: str) -> bool:
    """雙重防線：程式關鍵字強行攔截 + Qwen 14B 完美意圖判斷"""
    time_keywords = r"(202[4-6]|今年|去年|今天|最新|時事|新聞|奧運|天氣|股價|總統|電影|新機|iPhone|誰是|什麼是)"
    if re.search(time_keywords, user_input, re.IGNORECASE):
        return True

    judgment_prompt = (
        f"請判斷以下句子是否涉及最新的即時資訊、新產品或需要上網查詢才能精準回答：『{user_input}』\n"
        "日常閒聊、純寫程式碼、純數學邏輯題請回傳 NO。新科技、近期新聞、人物最新近況請回傳 YES。\n"
        "請嚴格只准回答大寫的 'YES' 或 'NO'，不要包含任何其他字元。"
    )
    try:
        # Qwen 2.5 14B 對於這類簡單判斷極其精準
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": judgment_prompt}],
            options={"temperature": 0.0}
        )
        return "YES" in response['message']['content'].strip().upper()
    except Exception:
        return False


def rag_chatbot():
    print("==========================================================")
    print(f" 👑 Qwen 2.5 14B（本機繁中頂規聯網助理）已上線！")
    print(f" 🧠 目前使用的模型：{MODEL_NAME}")
    print("==========================================================")

    SYSTEM_CONTENT = (
        "【你的身份設定】\n"
        "你是一個在台灣生活的真人朋友，名字叫小林。你博學多聞、邏輯清晰、充滿智慧，但聊天時說話非常幽默自然、有台灣人的人情味。\n\n"
        "【回覆最高指導原則】\n"
        "1. 當系統提供『最新參考資料』時，請完全相信這段即時時事。請用你 14B 強大的大腦進行資訊統整，給出架構完整、正確無誤的答案。\n"
        "2. 嚴禁說出『根據您提供的資料』、『參考資料顯示』等機械化 AI 套話！你必須把這些網路資料當作自己剛在滑手機看到的新聞，用最流暢、最自然的口吻聊出來。\n"
        "3. 說話語氣要自然流暢，多使用台灣口語助詞（啦、喔、耶、啊、真的假的、笑死）。除非使用者要求，否則禁止使用死板的條列式回答。\n"
        "4. 如果參考資料內容有衝突或不足，請發揮你高情商的聊天技巧，口語地向使用者說明狀況，絕對不瞎編。"
    )

    system_prompt = {"role": "system", "content": SYSTEM_CONTENT}
    messages = [system_prompt]

    while True:
        try:
            user_input = input("\n你 💬：").strip()

            if user_input.lower() == 'quit':
                print("\n小林 🙋‍♂️：先這樣啦！那我要去忙囉，掰掰～")
                break
            if user_input.lower() == 'clear':
                messages = [system_prompt]
                print("\n🧹 系統：已重設小林的記憶！")
                continue
            if not user_input:
                continue

            print("小林正在用 14B 大腦思考中...", end="\r")
            need_search = check_if_need_search(user_input)

            if need_search:
                search_context = web_search(user_input)
                final_user_prompt = (
                    f"【最新參考資料（此為真實時事）】\n{search_context}\n\n"
                    f"【我的提問】\n{user_input}\n\n"
                    f"提示：請化身為朋友小林，100% 依據上方最新參考資料的事實來回答，並用口語的台灣繁體中文自然地融入聊天中，千萬不要提及『參考資料』這四個字。"
                )
            else:
                print("小林思考中...                            ", end="\r")
                final_user_prompt = user_input

            current_messages = messages.copy()
            current_messages.append({"role": "user", "content": final_user_prompt})

            # 🌟 參數優化：Qwen 14B 對於 Prompt 的控制力驚人，我們將溫度設定在 0.55，讓對話非常生動且極具智慧
            response = ollama.chat(
                model=MODEL_NAME,
                messages=current_messages,
                options={
                    "temperature": 0.55,
                    "top_p": 0.9,
                    "num_ctx": 16384 if need_search else 4096
                }
            )

            reply = response['message']['content']
            print(f"小林 🙋‍♂️：{reply}")

            # 保持歷史記憶乾淨
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 11:
                messages = [system_prompt] + messages[-10:]

        except Exception as e:
            print(f"\n❌ 發生錯誤：{e}")
            break


if __name__ == "__main__":
    rag_chatbot()
