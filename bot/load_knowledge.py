# bot/load_knowledge.py
import os
from rag import SmartHotelRAG


def split_into_chunks(text: str, max_len: int = 700) -> list[str]:
    """
    Простой разрез текста на чанки, чтобы RAG работал точнее.
    Рубим по абзацам и потом по длине.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []

    for p in paragraphs:
        if len(p) <= max_len:
            chunks.append(p)
        else:
            # слишком длинный абзац — режем по max_len символов
            start = 0
            while start < len(p):
                part = p[start:start + max_len]
                chunks.append(part.strip())
                start += max_len

    return chunks


def load_files():
    rag = SmartHotelRAG()
    knowledge_dir = "knowledge"

    if not os.path.isdir(knowledge_dir):
        print(f"Папка {knowledge_dir} не найдена")
        return

    files = [f for f in os.listdir(knowledge_dir) if f.endswith(".txt")]
    if not files:
        print("Нет .txt файлов в папке knowledge/")
        return

    total_chunks = 0

    for filename in files:
        path = os.path.join(knowledge_dir, filename)

        # hotel_id берём из имени файла: EcoHouse.txt → EcoHouse
        hotel_id = os.path.splitext(filename)[0]

        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        chunks = split_into_chunks(text)
        print(f"{filename}: разрезали на {len(chunks)} чанков")

        ids = [f"{hotel_id}_{i}" for i in range(len(chunks))]

        rag.collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=[{"hotel": hotel_id} for _ in chunks],
        )

        total_chunks += len(chunks)
        print(f"✅ Загружено {len(chunks)} чанков для отеля {hotel_id}")

    print(f"🧮 Всего фрагментов во всех отелях: {total_chunks}")


if __name__ == "__main__":
    load_files()
