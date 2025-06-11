import os
import time
from pathlib import Path

import faiss  # type: ignore
import numpy as np
from dotenv import load_dotenv  # type: ignore
from openai import OpenAI
from PyPDF2 import PdfReader  # type: ignore
from sentence_transformers import SentenceTransformer

PDF_URL = "https://www.ipa.go.jp/jinzai/ics/core_human_resource/final_project/2024/f55m8k0000003spo-att/f55m8k0000003svn.pdf"
PDF_PATH = Path("data/ipa_guidelines.pdf")
INDEX_PATH = Path("output/ipa_rag_faiss")

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


def build_index(model: SentenceTransformer):
    """Create or load a FAISS index from the PDF."""
    index_file = INDEX_PATH.with_suffix(".faiss")
    text_file = INDEX_PATH.with_suffix(".txt")
    if index_file.exists() and text_file.exists():
        index = faiss.read_index(str(index_file))
        with open(text_file, "r", encoding="utf-8") as f:
            texts = [line.rstrip("\n") for line in f]
        return index, texts

    reader = PdfReader(str(PDF_PATH))
    all_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    chunk_size = 300
    texts = [all_text[i : i + chunk_size] for i in range(0, len(all_text), chunk_size)]
    embeddings = model.encode(texts, show_progress_bar=False)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype("float32"))
    Path("output").mkdir(exist_ok=True)
    faiss.write_index(index, str(index_file))
    with open(text_file, "w", encoding="utf-8") as f:
        for t in texts:
            f.write(t.replace("\n", " ") + "\n")
    return index, texts


def answer_with_llm(context: str, question: str, model: str = "gpt-4o") -> str:
    client = OpenAI()
    messages = [
        {"role": "system", "content": "以下のコンテキストに基づいて質問に答えてください。"},
        {"role": "user", "content": f"コンテキスト:\n{context}\n\n質問: {question}"},
    ]
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content.strip()


def answer_questions(index, texts, model: SentenceTransformer) -> None:
    md_lines = []
    for q in QUESTIONS:
        start = time.time()
        q_vec = model.encode([q])
        distances, idxs = index.search(np.array(q_vec).astype("float32"), 8)
        retrieval_time = time.time() - start
        context = "\n\n".join(texts[i] for i in idxs[0])
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
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    index, texts = build_index(model)
    answer_questions(index, texts, model)


if __name__ == "__main__":
    main()
