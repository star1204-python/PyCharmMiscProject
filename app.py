import os
import sys
import google.genai as genai
from google.genai import types
from PIL import Image
# ✨ 引入內建的視窗元件
import tkinter as tk
from tkinter import filedialog


def get_image_path_via_window():
    """隱藏 tkinter 主視窗，並彈出檔案選擇對話框"""
    root = tk.Tk()
    root.withdraw()  # 隱藏大背景視窗
    root.attributes('-topmost', True)  # 讓選檔案視窗強制顯示在最上層

    # 彈出選取檔案視窗
    file_path = filedialog.askopenfilename(
        title="請選擇一張圖片讓 AI 觀看",
        filetypes=[("圖片檔案", "*.png *.jpg *.jpeg *.webp *.bmp")]
    )
    return file_path


def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ 錯誤：找不到環境變數 GEMINI_API_KEY。")
        return

    client = genai.Client()

    config = types.GenerateContentConfig(
        system_instruction="你是一位貼心、專業且幽默的 AI 聊天助手。你擁有聯網能力，同時也能看懂使用者傳給你的圖片。請一律使用繁體中文（台灣）回答，並適度加入 emoji。",
        temperature=0.7,
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )

    try:
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=config
        )
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return

    print("==================================================")
    print("👁️ 視覺多模態 + 🌐 聯網型 AI 助手已連線！")
    print("👉 正常輸入文字：直接與 AI 聊天。")
    print("👉 想要傳送圖片：請直接在對話框輸入 'image' 或 '圖片'。")
    print("👉 輸入 'exit' 或 'quit' 即可結束對話。")
    print("==================================================\n")

    while True:
        try:
            # 讀取使用者輸入
            user_input = input("👤 你：").strip()

            if user_input.lower() in ['exit', 'quit']:
                print("\n🤖 AI 助手：下次見囉！祝你今天過得愉快！👋")
                break

            if not user_input:
                continue

            # ✨ 核心視覺邏輯：當使用者輸入 image 或 圖片 時，彈出視窗
            if user_input.lower() in ['image', '圖片']:
                print("📁 正在打開檔案選擇視窗，請點選圖片...")
                clean_path = get_image_path_via_window()

                if clean_path and os.path.exists(clean_path):
                    try:
                        img = Image.open(clean_path)
                        print(f"📸 已成功讀取圖片：{os.path.basename(clean_path)}")

                        prompt = input("💬 你想問這張圖片什麼？(直接按 Enter 預設為'幫我詳細描述這張圖'): ").strip()
                        if not prompt:
                            prompt = "請幫我詳細描述這張圖片裡有什麼？"

                        print("🤖 AI 正在分析圖片中...")
                        response = chat.send_message([img, prompt])
                        print(f"\n🤖 AI：{response.text}\n")

                    except Exception as img_err:
                        print(f"❌ 圖片處理失敗: {img_err}\n")
                else:
                    print("⚠️ 你取消了選擇，或檔案不存在。\n")

            else:
                # 📜 普通聊天
                response = chat.send_message(user_input)
                print(f"🤖 AI：{response.text}\n")

            # 🧠 自動限制記憶長度
            MAX_HISTORY = 10
            current_history = chat.get_history()
            if len(current_history) > MAX_HISTORY:
                chat._history = current_history[-MAX_HISTORY:]

        except KeyboardInterrupt:
            print("\n\n🤖 AI 助手：對話被強制中斷，再見！")
            break
        except Exception as e:
            print(f"\n❌ 發生錯誤: {e}\n")


if __name__ == "__main__":
    main()
