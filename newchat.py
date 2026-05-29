import datetime
import json
import os
import re

import jieba  # 中文分詞
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def tokenize(text):
    """中文分詞"""
    return list(jieba.cut(text))


class AILearningChatBot:
    """使用機器學習的智能聊天機器人"""

    def __init__(self, name="AI小辰", memory_file="ai_memory.json"):
        self.name = name
        self.user_name = None
        self.memory_file = memory_file

        # 載入記憶
        self.knowledge = self.load_memory()

        # 初始化向量化器
        self.vectorizer = TfidfVectorizer(tokenizer=tokenize)
        self.update_model()

    def load_memory(self):
        """載入記憶"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        return {
            "qa_pairs": {
                "你好": "你好啊！有什麼我可以幫你的嗎？",
                "你是誰": "我是AI小辰，一個會學習的聊天機器人～",
                "天氣": "我目前還看不到天氣，但你可以教我怎麼回答！",
                "再見": "掰掰！下次見！",
            },
            "learned_info": {},
        }

    def save_memory(self):
        """儲存記憶"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, ensure_ascii=False, indent=2)

    def update_model(self):
        """更新AI模型"""
        if len(self.knowledge["qa_pairs"]) > 1:
            questions = list(self.knowledge["qa_pairs"].keys())
            self.question_vectors = self.vectorizer.fit_transform(questions)
            self.questions = questions
        else:
            self.question_vectors = None
            self.questions = []

    def find_similar_question(self, user_input, threshold=0.3):
        """尋找相似的問題"""
        if self.question_vectors is None or len(self.questions) == 0:
            return None

        try:
            # 轉換用戶輸入
            input_vector = self.vectorizer.transform([user_input])

            # 計算相似度
            similarities = cosine_similarity(input_vector, self.question_vectors)[0]

            # 找到最相似的
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]

            if best_score > threshold:
                return self.questions[best_idx], best_score
        except:
            pass

        return None

    def learn_qa(self, question, answer):
        """學習問答對"""
        self.knowledge["qa_pairs"][question] = answer
        self.save_memory()
        self.update_model()
        return f"✅ 學會了！「{question}」→「{answer}」"

    def get_response(self, user_input):
        """獲取回應"""
        text = user_input.strip()

        # === 教學模式 ===
        if text.startswith("學:"):
            parts = text[2:].split("答:")
            if len(parts) == 2:
                q = parts[0].strip()
                a = parts[1].strip()
                return self.learn_qa(q, a)
            return "格式錯誤！請用「學:問題 答:答案」"

        # === 基本對話 ===
        # 打招呼
        if any(w in text.lower() for w in ['你好', '嗨', '哈囉', 'hello', 'hi']):
            if self.user_name:
                return f"嗨 {self.user_name}！"
            return "嗨！我是AI小辰，你叫什麼名字？"

        # 記住名字
        name_match = re.search(r'我叫(.+?)(?:[，。！？\s]|$)', text)
        if name_match:
            self.user_name = name_match.group(1).strip()
            return f"你好 {self.user_name}！我會記住你的"

        # 問時間
        if any(w in text for w in ['幾點', '時間']):
            return datetime.datetime.now().strftime("現在是 %H:%M:%S")

        # 道別
        if any(w in text for w in ['再見', '掰掰', 'bye']):
            return f"掰掰！下次見！"

        # === AI 語意理解 ===
        result = self.find_similar_question(text)
        if result:
            question, score = result
            answer = self.knowledge["qa_pairs"][question]
            return f"(相似度: {score:.0%}) {answer}"

        # === 如果都不匹配 ===
        return "這個問題我還沒學過，教我吧！用法：「學:你的問題 答:我的回答」"

    def chat(self):
        """開始對話"""
        print(f"\n{'=' * 55}")
        print(f"  🤖 {self.name} 上線了！(AI學習版)")
        print(f"  教學指令：「學:問題 答:答案」")
        print(f"  目前知識庫有 {len(self.knowledge['qa_pairs'])} 個問答")
        print(f"{'=' * 55}\n")

        while True:
            try:
                user_input = input("你: ").strip()
                if not user_input:
                    continue

                response = self.get_response(user_input)
                print(f"{self.name}: {response}\n")

                if any(w in user_input for w in ['再見', '掰掰', 'bye']):
                    break

            except KeyboardInterrupt:
                print(f"\n{self.name}: 掰掰～\n")
                break


if __name__ == "__main__":
    bot = AILearningChatBot()
    bot.chat()