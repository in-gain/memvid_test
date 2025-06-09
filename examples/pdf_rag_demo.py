import os
import argparse
import requests
from dotenv import load_dotenv
from memvid import MemvidEncoder
from memvid.index import IndexManager
from openai import OpenAI



def download_pdf(url: str, path: str):
    if not os.path.exists(path):
        print(f"Downloading PDF from {url}...")
        resp = requests.get(url)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(resp.content)
        print(f"Saved PDF to {path}")


def build_index(pdf_path: str) -> IndexManager:
    encoder = MemvidEncoder()
    encoder.add_pdf(pdf_path)
    chunks = encoder.chunks
    frame_numbers = list(range(len(chunks)))
    index = IndexManager()
    index.add_chunks(chunks, frame_numbers, show_progress=False)
    return index


def search_document(index: IndexManager, query: str, top_k: int = 5,
                    use_llm: bool = False, llm_model: str = "gpt-4o"):
    print(f"\nQuery: {query}")
    results = index.search(query, top_k)
    texts = []
    for rank, (chunk_id, dist, meta) in enumerate(results, 1):
        text_preview = meta["text"].replace("\n", " ")[:120]
        texts.append(meta["text"])
        print(f"{rank}. [ID {chunk_id} | Score {dist:.3f}] {text_preview}")

    if use_llm:
        context = "\n\n".join(texts)
        try:
            answer = answer_with_llm(context, query, llm_model)
            print("\nLLM回答:", answer)
        except Exception as e:
            print(f"LLM呼び出しに失敗しました: {e}")


def answer_with_llm(context: str, question: str, model: str = "gpt-4o") -> str:
    """Generate an answer using OpenAI based on provided context."""
    client = OpenAI()
    messages = [
        {"role": "system", "content": "以下のコンテキストに基づいて質問に答えてください。"},
        {"role": "user", "content": f"コンテキスト:\n{context}\n\n質問: {question}"},
    ]
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content.strip()


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="RAG search demo using a PDF")
    parser.add_argument("--url", required=True, help="PDF URL to download")
    parser.add_argument("--pdf", default="data/doc.pdf", help="Local path to save the PDF")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to show")
    parser.add_argument("--use-llm", action="store_true", help="Generate answers with OpenAI")
    parser.add_argument("--llm-model", default="gpt-4o", help="OpenAI model to use")
    args = parser.parse_args()

    download_pdf(args.url, args.pdf)
    index = build_index(args.pdf)
    print("\n✅ Index built. Enter your query (or empty to exit).")
    while True:
        try:
            query = input("\n> ").strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            break
        if not query:
            break
        search_document(index, query, args.top_k, args.use_llm, args.llm_model)


if __name__ == "__main__":
    main()
