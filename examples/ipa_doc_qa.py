import os
import time
from pathlib import Path
from dotenv import load_dotenv  # type: ignore
from memvid import MemvidEncoder, MemvidChat


def chat_with_metrics(chat: MemvidChat, message: str):
    """Send a message and return the answer with timing metrics."""
    start = time.time()
    context = chat._get_context(message)  # noqa: SLF001 - use internal method
    retrieval_time = time.time() - start

    if not chat.llm_client:
        answer = chat._generate_context_only_response(message)
        return answer, {"retrieval_time": retrieval_time, "llm_time": 0.0}

    messages = chat._build_messages(message, context)
    chat.conversation_history.append({"role": "user", "content": message})
    start_llm = time.time()
    answer = chat.llm_client.chat(messages)
    llm_time = time.time() - start_llm
    if answer:
        chat.conversation_history.append({"role": "assistant", "content": answer})
    else:
        answer = "Sorry, I encountered an error generating a response."

    return answer, {"retrieval_time": retrieval_time, "llm_time": llm_time}

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
    chat = MemvidChat(
        str(VIDEO_PATH),
        str(INDEX_PATH),
        llm_provider="openai",
        llm_model="gpt-4o",
        llm_api_key=os.environ.get("OPENAI_API_KEY"),
    )
    # Use more context chunks for better accuracy
    chat.context_chunks = 8

    md_lines = []
    for q in QUESTIONS:
        answer, metrics = chat_with_metrics(chat, q)
        md_lines.append(f"### Q: {q}")
        md_lines.append("")
        md_lines.append(answer)
        md_lines.append("")
        md_lines.append(f"- RAG解析時間: {metrics['retrieval_time']:.2f}秒")
        md_lines.append(f"- LLM応答時間: {metrics['llm_time']:.2f}秒")
        md_lines.append("")

    output_text = "\n".join(md_lines)
    Path("output").mkdir(exist_ok=True)
    with open("output/ipa_answers.md", "w", encoding="utf-8") as f:
        f.write(output_text)

    print(output_text)


def main():
    load_dotenv()
    download_pdf()
    build_memory()
    answer_questions()


if __name__ == "__main__":
    main()
