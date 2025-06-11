import os
import time
from pathlib import Path
from dotenv import load_dotenv  # type: ignore
from memvid import MemvidEncoder
from memvid.index import IndexManager
from openai import OpenAI

PDF_URL = "https://www.ipa.go.jp/jinzai/ics/core_human_resource/final_project/2024/f55m8k0000003spo-att/f55m8k0000003svn.pdf"
PDF_PATH = Path("data/ipa_guidelines.pdf")
INDEX_PATH = Path("output/ipa_rag_index")

QUESTIONS = [
    "この資料の概要を教えてください。",
    "生成AIを企業が利用する上で重要なことを教えてください。",
    "生成AIにおけるリスク管理をどのように扱うべきですか？",
]


def download_pdf() -> None:
    if not PDF_PATH.exists():
        import requests

        PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {PDF_URL} ...")
        resp = requests.get(PDF_URL)
        resp.raise_for_status()
        with open(PDF_PATH, "wb") as f:
            f.write(resp.content)
        print(f"Saved to {PDF_PATH}")


def build_index() -> IndexManager:
    if INDEX_PATH.with_suffix(".faiss").exists():
        index = IndexManager()
        index.load(str(INDEX_PATH))
        return index

    encoder = MemvidEncoder()
    encoder.add_pdf(str(PDF_PATH))
    index = IndexManager()
    index.add_chunks(encoder.chunks, list(range(len(encoder.chunks))), show_progress=False)
    Path("output").mkdir(exist_ok=True)
    index.save(str(INDEX_PATH))
    return index


def answer_with_llm(context: str, question: str, model: str = "gpt-4o") -> str:
    client = OpenAI()
    messages = [
        {"role": "system", "content": "以下のコンテキストに基づいて質問に答えてください。"},
        {"role": "user", "content": f"コンテキスト:\n{context}\n\n質問: {question}"},
    ]
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content.strip()


def answer_questions(index: IndexManager) -> None:
    md_lines = []
    for q in QUESTIONS:
        start = time.time()
        results = index.search(q, top_k=8)
        retrieval_time = time.time() - start
        context = "\n\n".join(meta["text"] for _, _, meta in results)
        llm_time = 0.0
        answer = context
        if os.environ.get("OPENAI_API_KEY"):
            start_llm = time.time()
            try:
                answer = answer_with_llm(context, q)
            except Exception as e:  # noqa: BLE001 - show raw error
                answer = f"LLM呼び出しに失敗しました: {e}"
            llm_time = time.time() - start_llm
        md_lines.append(f"### Q: {q}")
        md_lines.append("")
        md_lines.append(answer)
        md_lines.append("")
        md_lines.append(f"- RAG解析時間: {retrieval_time:.2f}秒")
        md_lines.append(f"- LLM応答時間: {llm_time:.2f}秒")
        md_lines.append("")

    output_text = "\n".join(md_lines)
    Path("output").mkdir(exist_ok=True)
    with open("output/ipa_baseline_answers.md", "w", encoding="utf-8") as f:
        f.write(output_text)
    print(output_text)


def main() -> None:
    load_dotenv()
    download_pdf()
    index = build_index()
    answer_questions(index)


if __name__ == "__main__":
    main()
