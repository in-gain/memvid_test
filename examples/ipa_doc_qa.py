import os
import time
from pathlib import Path
from dotenv import load_dotenv # type: ignore
from memvid import MemvidEncoder, MemvidChat

PDF_URL = "https://www.ipa.go.jp/jinzai/ics/core_human_resource/final_project/2024/f55m8k0000003spo-att/f55m8k0000003svn.pdf"
PDF_PATH = Path("data/ipa_guidelines.pdf")
VIDEO_PATH = Path("output/ipa_memory.mp4")
INDEX_PATH = Path("output/ipa_memory_index.json")

QUESTIONS = [
    "この資料の概要を教えてください。",
    "生成AIを企業が利用する上で重要なことを教えてください。",
    "生成AIにおけるリスク管理をどのように扱うべきですか？",
]

def download_pdf():
    if not PDF_PATH.exists():
        import requests
        PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {PDF_URL} ...")
        resp = requests.get(PDF_URL)
        resp.raise_for_status()
        with open(PDF_PATH, "wb") as f:
            f.write(resp.content)
        print(f"Saved to {PDF_PATH}")


def build_memory():
    if VIDEO_PATH.exists() and INDEX_PATH.exists():
        return
    encoder = MemvidEncoder()
    encoder.add_pdf(str(PDF_PATH))
    VIDEO_PATH.parent.mkdir(exist_ok=True)
    print("Building memory ...")
    encoder.build_video(str(VIDEO_PATH), str(INDEX_PATH), show_progress=False)


def answer_questions():
    chat = MemvidChat(str(VIDEO_PATH), str(INDEX_PATH), llm_provider="openai",llm_model="gpt-4o",llm_api_key=os.environ.get("OPENAI_API_KEY"))
    for q in QUESTIONS:
        start = time.time()
        answer = chat.chat(q)
        elapsed = time.time() - start
        print("Q:", q)
        print("A:", answer)
        print(f"回答時間: {elapsed:.2f}秒\n")


def main():
    load_dotenv()
    download_pdf()
    build_memory()
    answer_questions()

if __name__ == "__main__":
    main()
