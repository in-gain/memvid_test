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
\n## 5. PDF RAG Demo Script
This script allows dynamic PDF selection via command line arguments.
We executed it with the NEDO prize program PDF and issued two search
queries.

```bash
PYTHONPATH=. MEMVID_DUMMY_EMBEDDINGS=1 \
    python examples/pdf_rag_demo.py \
    --url https://www.nedo.go.jp/content/800025275.pdf \
    --pdf data/nedo_dynamic.pdf --top_k 2 <<'Q'
この文書の概要を教えてください
このプロジェクトの目的は何ですか？
Q
```
Actual output (truncated):
```text
Downloading PDF from https://www.nedo.go.jp/content/800025275.pdf...
Saved PDF to data/nedo_dynamic.pdf

✅ Index built. Enter your query (or empty to exit).

> Query: この文書の概要を教えてください
1. [ID 1 | Score 2386104.000] 発者やＡＩ提供 者※個人を含む ）と組んで応募すること とします 。具体的には 、以下の形態のいずれ でも応募することが可能です。   ➢ ユーザー と開発者が ペアを組んで ＡＩエージェントを開発・実証 する  ➢ ユーザー が内製で Ａ
2. [ID 0 | Score 2918268.000] 1   NEDO懸賞金活用型プログラム ／GENIAC-PRIZE  ～国産基盤モデ ル等を活用した 社会課題解決 ＡＩエージェント開発 ～    １．事業趣旨１．１． 背景及び 目的  ⚫ 生成ＡＩは、生産性・付加価値の向上等を通じて

> Query: このプロジェクトの目的は何ですか？
1. [ID 5 | Score 3122292.000] 、業界全体に対してイン パクトを持つか。   ユーザー の  変革 ・ユーザーの業務プロセス改革が、効果的に実施できてい るか。事業部門・情報システム等関係部門の連携が有機的 に行われているか。    6   ・開発者とユーザーのコミュニケ
2. [ID 7 | Score 3370236.000] ても併せて提案書に記載してください。     ４．スケジュール   ⚫ 懸賞広告： 2025年５月９日  ⚫ 応募説明会： 2025年５月26日  ➢ 応募説明会の詳細は別添を参照してください。   ⚫ 応募期間：2025年６月～９月末まで
```

### 6. LLM Integration Attempt
The demo loads `.env` to pick up `OPENAI_API_KEY` and uses the `gpt-4o` model by default.
However, calling the API still failed due to a connection error.

```bash
PYTHONPATH=. MEMVID_DUMMY_EMBEDDINGS=1 \
    python examples/pdf_rag_demo.py \
    --url https://www.nedo.go.jp/content/800025275.pdf \
    --pdf data/nedo_llm_new.pdf --top_k 1 --use-llm --llm-model gpt-4o <<'Q'
概要は？
Q
```
Output snippet:
```text
Downloading PDF from https://www.nedo.go.jp/content/800025275.pdf...
Saved PDF to data/nedo_llm_new.pdf

✅ Index built. Enter your query (or empty to exit).

> Query: 概要は？
1. [ID 3 | Score 4266948.000] 事前審査 への応募が可 能となります のでご留意ください。   ➢ 応募後、事務局より開発状況のヒアリングをさせていただきます。   ➢ 提供データ    GENIACで構築している一部のデータ提供も 準備中です。各データの利用条件 等は
LLM呼び出しに失敗しました: Connection error.
```

### 7. LLM呼び出しの再試行
再度、OpenAI API への接続を試みましたが、以下のように `Method forbidden` エラーが表示され、
LLM を利用した回答生成には失敗しました。

```bash
PYTHONPATH=. MEMVID_DUMMY_EMBEDDINGS=1 \
    python examples/pdf_rag_demo.py \
    --url https://www.nedo.go.jp/content/800025275.pdf \
    --pdf data/nedo_new.pdf --top_k 1 --use-llm --llm-model gpt-4o <<'Q'
概要は？
Q
```
出力例:
```text
Downloading PDF from https://www.nedo.go.jp/content/800025275.pdf...
Saved PDF to data/nedo_new.pdf

✅ Index built. Enter your query (or empty to exit).

> Query: 概要は？
1. [ID 3 | Score 4266948.000] 事前審査 への応募が可 能となります のでご留意ください。   ➢ 応募後、事務局より開発状況のヒアリングをさせていただきます。   ➢ 提供データ    GENIACで構築している一部のデータ提供も 準備中です。各データの利用条件 等は
LLM呼び出しに失敗しました: Method forbidden
```
## 8. IPAドキュメントQAスクリプト実行結果

`examples/ipa_doc_qa.py` を実行して、ガイドラインPDFから質問に回答させました。環境変数 `MEMVID_DUMMY_EMBEDDINGS=1` を使用して埋め込み生成をスキップし、OpenAI API を利用しています。

```bash
PYTHONPATH=. MEMVID_DUMMY_EMBEDDINGS=1 python examples/ipa_doc_qa.py
```

出力された `output/ipa_answers.md` の内容を以下に抜粋します。

```markdown
### Q: この資料の概要を教えてください。

この資料は、生成AI（Generative AI）を組織内に導入および運用する際のガイドラインを示しています。特に、セキュリティリスクの評価と対策方法に焦点を当てています。資料の目的は、組織が生成AIを安全に利用し、不安なく効果的に活用できるようにすることです。

内容は以下の通りです：

1. **背景と目的**: 生成AIの急速な発展により、国家主導でその利用が推進されていますが、多くの組織は導入に不安を感じています。それらの不安を解消することで、安全な導入と運用を促進します。

2. **導入における課題**: 多くの企業が導入時に課題を感じており、課題は多岐にわたります。この原因として、生成AIの理解不足が挙げられています。

3. **セキュリティ対策**: 生成AIシステムの導入にあたり、リスクアセスメントが重要です。具体的には、モデル利用の方法論、プロンプトエンジニアリング、入力制限、出口対策、および多層防御の戦略が述べられています。

4. **チェックリスト**: 安全な運用を確保するためには、ガバナンスとシステムの観点からチェックリストを作成し、対策漏れがないようにする必要があります。

5. **ガードレールの実装**: OSSのNeMo Guardrailsを使用した実証実験の実施など、生成AIに対する具体的なセキュリティ対策が紹介されています。

6. **今後の展望**: 生成AIの活用が増えるにつれ、攻撃の高度化が懸念されるため、継続的なリスクマネジメントとセキュリティ対策が求められるとしています。

この資料を通じて、組織は生成AIのリスクを認識し、適切な対策を講じて、安全かつ効果的に生成AIを利用できるようになることを目指しています。

- RAG解析時間: 0.09秒
- LLM応答時間: 10.77秒

### Q: 生成AIを企業が利用する上で重要なことを教えてください。

企業が生成AIを利用する際に重要な点はいくつかあります。以下に主要なポイントを挙げます。

1. **セキュリティリスクの管理**: 生成AI導入に際しては、セキュリティリスクの評価が不可欠です。特に、個人情報や組織の機密情報が漏洩しないようにするための仕組みを整える必要があります（Context 4, 7）。

2. **ガイドライン策定**: 生成AIの利活用ガイドラインを策定することは、企業全体での統一的な利用を促します。具体的な利用方法やプロンプトの設計方法などをガイドラインにまとめ、ユーザーの適切な利用を支援することが重要です（Context 1, 4）。

3. **ユーザー教育**: AIの出力を正しく解釈し、その限界を理解するための社員教育は非常に重要です。AIの出力の正確性を常に確認する習慣をつけ、誤情報やバイアスを減らす努力が必要です（Context 2, 5）。

4. **透明性と信頼性の確保**: 生成AIの更新管理を行い、透明性を保つことが重要です。また、ユーザーとの間で評価とフィードバックを行い、生成AIの信頼性を高めるための継続的な改善を意識することが求められます（Context 2, 6）。

5. **業務効率化と品質向上の評価**: 生成AI導入による業務効率化や品質向上の効果を定量的、定性的に評価することが必要です。具体的な評価手法を確立し、その効果を測ることで、導入の目的達成度を確認できます（Context 8）。

企業がこれらのポイントを考慮しながら生成AIを導入、運用することで、安全かつ効果的な活用が可能になるでしょう。

- RAG解析時間: 0.11秒
- LLM応答時間: 11.34秒

### Q: 生成AIにおけるリスク管理をどのように扱うべきですか？

生成AIにおけるリスク管理は、企業が生成AIを安全かつ効果的に活用するために非常に重要です。以下にリスク管理の主要なポイントを示します。

1. **リスクアセスメントの実施**: 生成AIを導入する際には、まずリスクアセスメントを実施して潜在的なリスクを特定します。組織が保有する資産を棚卸しし、外部からのリスク（例えばフィッシング攻撃やDoS攻撃）や内部からのリスク（ユーザーの過失など）を洗い出します（Context 2）。

2. **セキュリティ対策の強化**: 特にデータの浄化と厳格なユーザー・ポリシーが重要であり、また、不正なコード実行を防ぐため、プラグインやアクセスコントロールを強化します（Context 2）。

3. **過度な信頼を避ける**: 生成AIの出力を盲信せず、必ず内容を確認することが必要です。過度にAIに依存すると、不正確な情報や法的問題に発展するリスクがあります（Context 5）。

4. **モデルの管理と保護**: 独自の生成AIモデルやデータベースへの不正アクセスを防ぐため、厳重なセキュリティ対策（例えばアクセス制御や暗号化）を実施します。このような対策により、モデルの盗難や情報漏洩を防ぎます（Context 2）。

5. **従業員の教育とガイドラインの策定**: 従業員に生成AIの正しい利用法や注意点を教育します。また、生成AIの利用に関するガイドラインを制定し、社員がそれに従えるようにします（Context 3）。

6. **コンプライアンスと規制の遵守**: GDPRやAI規制法など、国際的な規制を遵守し、必要に応じてコンプライアンスチェックを行います。特に、リスクベース・アプローチによるAI管理を実践し、透明性を確保します（Context 8）。

これらのポイントを実践し、生成AIを利用する際に常にセキュリティとコンプライアンスを意識することで、企業はより安全にAIを活用できるでしょう。

- RAG解析時間: 0.12秒
- LLM応答時間: 15.15秒

```
