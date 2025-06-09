# Memvid 検証手順

この手順では、NEDOの公募要領PDFを用いて Memvid ライブラリの基本機能を確認します。

## 1. PDFをダウンロード

```bash
wget https://www.nedo.go.jp/content/800025275.pdf -O nedo.pdf
```
実行結果:
```
--2025-06-09 06:20:37--  https://www.nedo.go.jp/content/800025275.pdf
Resolving proxy (proxy)... 172.20.0.3
Connecting to proxy (proxy)|172.20.0.3|:8080... connected.
Proxy request sent, awaiting response... 200 OK
Length: 298626 (292K) [application/pdf]
Saving to: ‘nedo.pdf’

nedo.pdf            100%[===================>] 291.63K   495KB/s    in 0.6s

2025-06-09 06:20:39 (495 KB/s) - ‘nedo.pdf’ saved [298626/298626]
```

## 2. ビデオメモリを作成

`MemvidEncoder` を使って PDF を読み込み、QR コードの動画とインデックスを生成します。モデルのダウンロードを省略するため、環境変数 `MEMVID_DUMMY_EMBEDDINGS=1` を設定しておきます。

```python
from memvid import MemvidEncoder

encoder = MemvidEncoder()
encoder.add_pdf("nedo.pdf")
stats = encoder.build_video("nedo.mp4", "nedo_index.json", show_progress=False)
print(stats)
```
実行結果:
```
Using dummy embeddings instead of sentence-transformers.
🐛 FRAMES: 9 files in /tmp/tmp80gyd441/frames
🐛 FFMPEG: frames=/tmp/tmp80gyd441/frames → docker_mount=/tmp/tmp80gyd441
/workspace/memvid_test/memvid/encoder.py:493: UserWarning: h265 encoding failed:  Invalid suffix 'mkv'. Falling back to MP4V.
  warnings.warn(f"{codec} encoding failed: {e}. Falling back to MP4V.", UserWarning)
{'backend': 'opencv', 'codec': 'mp4v', 'total_frames': 9, 'video_size_mb': 0.5000419616699219, 'fps': 15, 'duration_seconds': 0.6, 'total_chunks': 9, 'video_file': 'nedo.mp4', 'index_file': 'nedo_index.json', 'index_stats': {'total_chunks': 9, 'total_frames': 9, 'index_type': 'Flat', 'embedding_model': 'all-MiniLM-L6-v2', 'dimension': 384, 'avg_chunks_per_frame': 1.0}}
```
通常、`stats["duration_seconds"]` にはおよそ 20〜30 秒程度の値が入ります。

## 3. メモリを検索

動画とインデックスを生成したら、`MemvidRetriever` を初期化してセマンティック検索を試します。

```python
from memvid import MemvidRetriever

retriever = MemvidRetriever("nedo.mp4", "nedo_index.json")
for q in ["概要", "目的", "技術的特徴", "期待される効果"]:
    print("Query:", q)
    for r in retriever.search(q):
        print(r[:60])
    print("-" * 20)
```
実行結果（抜粋）:
```
Using dummy embeddings instead of sentence-transformers.
Query: 概要
pyzbar decode failed: Unable to find zbar shared library
ても併せて提案書に記載してください。
...
--------------------
Query: 目的
pyzbar decode failed: Unable to find zbar shared library
ロトタイプ の選定
...
--------------------
```

## 4. 対話モードを開始

`MemvidChat` にメモリを読み込むことで対話セッションを開始できます。LLM の API キーを設定しない場合、コンテキストのみの出力となります。

```python
from memvid import MemvidChat

chat = MemvidChat("nedo.mp4", "nedo_index.json", llm_api_key=None)
chat.start_session()
print("User: 概要")
print("Assistant:", chat.chat("概要"))
```
実行結果（抜粋）:
```
✗ Failed to initialize LLM client: No API key found for google. Please set one of: ['GOOGLE_API_KEY']
LLM not available - will return context only.
--------------------------------------------------
User: 概要
Assistant: Based on the knowledge base, here's what I found:
1. ても併せて提案書に記載してください.
...
```
