import os
import json
from typing import List, Dict


KNOWLEDGE_DIR = "knowledge"


class SmartHotelRAG:
    """
    Лёгкая RAG-система без chromadb.
    Загружает знания из файлов и делает простой поиск по тексту.
    """

    def __init__(self):
        self.knowledge = {}  # {hotel_name: [chunks]}
        self.load_all()

    # ---------------------------------------------------------
    # Загрузка всех файлов
    # ---------------------------------------------------------
    def load_all(self):
        if not os.path.exists(KNOWLEDGE_DIR):
            print("❌ Папка knowledge/ не найдена")
            return

        for filename in os.listdir(KNOWLEDGE_DIR):
            if not filename.endswith(".txt") and not filename.endswith(".json"):
                continue

            hotel = filename.replace(".txt", "").replace(".json", "")

            filepath = os.path.join(KNOWLEDGE_DIR, filename)
            text = self._read_file(filepath)

            chunks = self._split_chunks(text)
            self.knowledge[hotel] = chunks

            print(f"📚 {hotel}: загружено {len(chunks)} фрагментов")

    # ---------------------------------------------------------
    def _read_file(self, path: str) -> str:
        if path.endswith(".json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("text", "")
            except:
                return ""
        else:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                return ""

    # ---------------------------------------------------------
    # Разбиение на блоки (чтобы ГигаЧату было проще)
    # ---------------------------------------------------------
    def _split_chunks(self, text: str, min_len: int = 40) -> List[str]:
        lines = text.split("\n")
        chunks = [l.strip() for l in lines if len(l.strip()) >= min_len]
        return chunks

    # ---------------------------------------------------------
    # Основной метод поиска
    # ---------------------------------------------------------
    def query(self, question: str, hotel: str = None, top_k: int = 3) -> str:

        if not hotel:
            return ""

        hotel = hotel.lower()

        if hotel not in (h.lower() for h in self.knowledge.keys()):
            return ""

        # Находим реальный ключ (чтобы не было ошибки регистра)
        for h in self.knowledge:
            if h.lower() == hotel:
                hotel = h
                break

        chunks = self.knowledge.get(hotel, [])

        # простой поиск по ключевым словам
        q = question.lower()
        scored: List[Dict] = []

        for ch in chunks:
            score = 0
            for word in q.split():
                if word in ch.lower():
                    score += 1
            if score > 0:
                scored.append({"score": score, "text": ch})

        if not scored:
            return ""

        # сортировка по релевантности
        scored = sorted(scored, key=lambda x: x["score"], reverse=True)

        # берём лучшие k
        best = [s["text"] for s in scored[:top_k]]
        return "\n".join(best)


# ---------------------------------------
# тест
# ---------------------------------------
if __name__ == "__main__":
    rag = SmartHotelRAG()
    print("\n=== TEST ===")
    print(rag.query("есть ли парковка?", hotel="EcoHouse"))
