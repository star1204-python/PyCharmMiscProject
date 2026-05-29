import os
import re
import ollama
from duckduckgo_search import DDGS

MODEL_NAME = "qwen2.5:7b"


def clean_web_text(text: str) -> str:
    """清理網頁內文，移除無意義的空白與特殊符號，降低 AI 閱讀負擔"""
    if not text:
        return ""
    # 移除 HTML 標籤、多餘的換行與空白
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    # 限制單一網頁只保留前 400 個字（對 7B 模型來說，精簡才是關鍵）
    return text[:400].strip()


def web_search(query: str, max_results: int = 3) -> str:
    """2026 最新版 DuckDuckGo 安全檢索 + 深度內容過濾"""
    print(f"🔍 [聯網中] 正在即時抓取最新網路資料：'{query}' ...")
    try:
        results = []
        with DDGS() as ddgs:
            # 確保使用最新 8.x.x 版的產生器讀取方式
            ddgs_generator = ddgs.text(query, max_results=max_results)
            results = list(ddgs_generator)

        if not results:
            return "（網路暫時沒有查到該事件的即時資訊）"

        context_list = []
        for i, res in enumerate(results, 1):
            title = res.get('title', '無標題')
            # 🌟 關鍵修正：確實抓取 body 並進行去背清理
            body = clean_web_text(res.get('body', ''))

            context_list.append(f"【新聞來源 {i}：{title}】\n即時內容摘要：{body}")

        print(f"✅ 成功抓取並清理完成 {len(results)} 筆即時網頁資料！")
        return "\n\n".join(context_list)

    except Exception as e:
        print(f"⚠️ 聯網抓取失敗，原因：{e}")
        return "（搜尋引擎連線失敗，請依據你已知的知識回答）"


def check_if_need_search(user_input: str) -> bool:
    """雙重防線：程式關鍵字強行攔截 + AI 意圖判斷"""
    # 只要包含時間或時事關鍵字，直接強制上網，不聽 AI 的
    time_keywords = r"(202[4-6]|今年|去年|今天|最新|時事|新聞|奧運|天氣|股價|總統|電影|新機|iPhone)"
    if re.search(time_keywords, user_input, re.IGNORECASE):
        return True

    judgment_prompt = (
        f"請判斷以下句子是否涉及最新的即時資訊、新產品或需要上網查詢才能精準回答：『{user_input}』\n"
        "日常聊天、純程式碼、數學題請回答 NO。新科技、近期新聞、人物近況請回答 YES。\n"
        "只准回答 'YES' 或 'NO'。"
    )
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": judgment_prompt}],
            options={"temperature": 0.0}
        )
        return "YES" in response['message']['content'].strip().upper()
    except Exception:
        return False


def rag_chatbot():
    print("==================================================")
    print(f" 🥰 完美突破 2023 年限制！Ollama 聯網助理")
    print(f" 🧠 目前使用的模型：{MODEL_NAME}")
    print("==================================================")

    SYSTEM_CONTENT = (
        "你是一個在台灣生活的真人朋友，名字叫小林。你講話非常口語、自然且溫暖。\n"
        "【聯網回答最高準則】\n"
        "1. 系統如果提供『最新參考資料』，這絕對是真實發生的時事。請你『完全相信這段資料』，並用你自己的口吻把事實講出來。\n"
        "2. 不要用你 2023 年的舊記憶去反駁最新參考資料。如果參考資料寫的跟你原本知道的不一樣，請以參考資料為準！\n"
        "3. 絕對不要在回答中說出『根據您提供的資料』，要像你自己剛看完新聞一樣自然地聊出來。\n"
        "4. 講話要有人類溫度，多用台灣口語助詞（啦、喔、耶、啊），禁止生硬的條列式回答。"
    )

    system_prompt = {"role": "system", "content": SYSTEM_CONTENT}
    messages = [system_prompt]

    while True:
        try:
            user_input = input("\n你 💬：").strip()

            if user_input.lower() == 'quit':
                print("\n小林 🙋‍♂️：先這樣啦！下次聊，掰掰～")
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
                # 🌟 強勢灌輸：命令 AI 必須服從網路事實
                final_user_prompt = (
                    f"【最新參考資料（此為真實發生的時事）】\n{search_context}\n\n"
                    f"【我的提問】\n{user_input}\n\n"
                    f"請扮演小林，用口語的繁體中文，100% 依據上方最新參考資料的內容來回答我的問題。"
                )
            else:
                print("小林思考中...                  ", end="\r")
                final_user_prompt = user_input

            current_messages = messages.copy()
            current_messages.append({"role": "user", "content": final_user_prompt})

            response = ollama.chat(
                model=MODEL_NAME,
                messages=current_messages,
                options={
                    "temperature": 0.4,  # 降到 0.4，避免過高的溫度讓它無視網路資料
                    "top_p": 0.9,
                    "num_ctx": 8192 if need_search else 4096
                }
            )

            reply = response['message']['content']
            print(f"小林 🙋‍♂️：{reply}")

            # 保持記憶乾淨
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 11:
                messages = [system_prompt] + messages[-10:]

        except Exception as e:
            print(f"\n❌ 發生錯誤：{e}")
            break


if __name__ == "__main__":
    rag_chatbot()