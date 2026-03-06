# Vows (VoxFlow オープンソース版)

✨🎬🌍🚀 再現可能な AI 動画吹き替えパイプライン。

Languages: [简体中文](README.md) · [English](README_EN.md) · [日本語](README_JA.md)

## 🎯 プロジェクト概要

Vows は多言語 AI 吹き替え・翻訳のためのエンジニアリングパイプラインです。入力となる元動画を、選択したターゲット言語（50言語対応）で公開可能な完成動画へ変換することを目的としています。

単一モデルのデモスクリプトではありません。再現可能で、フォールバック可能で、拡張可能な完全システムです。

主な機能:

1. 音声の自動抽出とボーカル分離（背景干渉を低減）
2. ASR + 話者ダイアライゼーション（時系列・話者別にテキスト整理）
3. セグメント単位の LLM 翻訳（失敗時は原文フォールバック）
4. IndexTTS 音声クローン（失敗時は EdgeTTS 自動フォールバック）
5. タイムライン整合ミックスと出力（ハード字幕焼き込み対応）
6. スクリプト/API/ドラッグ&ドロップ bat の3モード対応

1行要約:

音声抽出 -> ボーカル分離 -> ASR + 話者ダイアライゼーション -> LLM 翻訳 -> TTS クローン/フォールバック -> ミックス & 出力

---

## 🆚 成果比較

### ケース1: TED（ハード字幕あり）
- 元動画:

https://github.com/user-attachments/assets/6d045aa6-6eec-4c29-8a7f-918809bea939

- 出力動画:

https://github.com/user-attachments/assets/ead60688-c0de-4ee9-983d-e3d9af182b16

比較ポイント:
1. 元動画のテンポとタイムラインを維持し、セグメント整合で吹き替え
2. 目標言語の吹き替えと可視字幕を同時に生成
3. 話者スタイルの近似を保ちつつ、失敗区間はフォールバックで完走

### ケース2: Trump（字幕なし）
- 元動画:

https://github.com/user-attachments/assets/b396c851-d8c8-44a2-ba6f-4cba41926812

- 出力動画:

https://github.com/user-attachments/assets/7b0c1728-c79d-4841-9d07-616031f63096

比較ポイント:
1. 字幕焼き込みなしの吹き替え動画を出力
2. 背景音と音声の自然な関係を維持して最終ミックス
3. 翻訳/クローンが一部失敗してもフォールバックでタスク完了可能

---

## 📚 ドキュメント

1. ファイル構成: `docs/FILES_ZH.md`
2. コンプライアンス: `docs/COMPLIANCE_ZH.md`

---

## 🧰 1. 動作要件（Windows）

1. OS: Windows 10/11
2. Python: 3.10 または 3.11
3. Conda: 推奨（Anaconda/Miniconda）
4. CUDA: 任意（NVIDIA GPU がある場合は推奨）
5. FFmpeg: システム PATH もしくは `tools/ffmpeg` で利用可能
6. Node.js: フロントエンド実行時のみ必要（Node 18+ 推奨）

---

## 📥 2. リポジトリをクローン

```powershell
git clone https://github.com/wkl1918/Vows
cd Vows
```

---

## 🐍 3. Python 環境作成とバックエンド依存のインストール

```powershell
conda create -n VoxFlow python=3.10 -y
conda activate VoxFlow
pip install -r backend/requirements.txt
```

---

## 🧠 4. IndexTTS2 の準備（別リポジトリ）

このリポジトリでは IndexTTS の重みやキャッシュを再配布しません。上流から準備してください:

1. 公式上流: `https://github.com/index-tts/index-tts`
2. 例として `D:\AI\index-tts-main` にクローン

3. `checkpoints` と依存ファイルをダウンロード

### Option A（推奨）: HuggingFace CLI

VoxFlow 環境で:

```powershell
conda activate VoxFlow
pip install -U "huggingface_hub[cli]"
```

ローカルディレクトリ準備:

```powershell
mkdir D:\AI -Force
cd D:\AI
git clone https://github.com/index-tts/index-tts.git index-tts-main
cd index-tts-main
```

モデルを `checkpoints` へダウンロード:

```powershell
hf download IndexTeam/IndexTTS-2 --local-dir checkpoints
```

中国本土でネットワークが遅い場合のミラー:

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
hf download IndexTeam/IndexTTS-2 --local-dir checkpoints
```

簡易検証:

```powershell
Test-Path D:\AI\index-tts-main\checkpoints\config.yaml
Test-Path D:\AI\index-tts-main\checkpoints\gpt.pth
Test-Path D:\AI\index-tts-main\checkpoints\s2mel.pth
```

すべて `True` になること。

4. `.env` で `INDEXTTS_DIR` を設定

`D:\Vows\backend\.env` を編集して以下を設定:

```env
INDEXTTS_DIR=D:/AI/index-tts-main
```

注意:
1. 実際のパスに合わせること。
2. Windows でも `/` 形式を推奨。
3. `checkpoints` ではなく `index-tts-main` ルートを指定。

5. バックエンド起動前の確認:

```powershell
python -c "import os; p=os.getenv('INDEXTTS_DIR'); print('INDEXTTS_DIR=',p)"
```

設定が正しければ、クローン段階の `IndexTTS config not found` は解消されます。

---

## ⚙️ 5. 環境変数の設定

まずテンプレートをコピー:

```powershell
Copy-Item backend/.env.example backend/.env
```

その後 `backend/.env` を最低限以下で編集:

```env
HF_TOKEN=hf_xxx
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
INDEXTTS_DIR=D:/AI/index-tts-main
```

説明:
1. `HF_TOKEN`: pyannote/huggingface へのアクセス用
2. `LLM_API_KEY`: 翻訳プロバイダ用（Qwen/DeepSeek/OpenAI互換）
3. `INDEXTTS_DIR`: ローカル IndexTTS コードのディレクトリ
4. 未設定時はクローンをスキップし EdgeTTS へフォールバック

必要ならプロキシ例:

```env
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
```

---

## 🚀 6. バックエンド起動

```powershell
conda activate VoxFlow
cd backend
python app.py
```

起動成功目安:

`Uvicorn running on http://127.0.0.1:8000`

---

## 💻 7. フロントエンド起動（任意）

```powershell
cd frontend
npm install
npm run dev
```

---

## 🧭 8. 実行方法

ターゲット言語の切り替えは3方式:

### 8.1 フロントエンドモード（最も簡単）
1. バックエンド起動: `python backend/app.py`
2. フロントエンド起動: `cd frontend && npm install && npm run dev`
3. ターゲット言語（50種）を選んで動画アップロード

### 8.2 bat ドラッグ&ドロップモード
1. 動画を以下へドラッグ:
- `一键处理视频.bat`（ハード字幕なし）
- `一键处理视频并加硬字幕.bat`（ハード字幕あり）
2. 第2引数が無い場合は言語コード選択を促す
3. CLI 直接指定も可能:

```powershell
一键处理视频.bat "D:\demo.mp4" en
一键处理视频并加硬字幕.bat "D:\demo.mp4" ja
```

### 8.3 Python スクリプトモード（最も制御しやすい）

```powershell
python run_task.py "D:/path/to/input.mp4" zh
python run_task_with_subtitles.py "D:/path/to/input.mp4" ja
```

第2引数はターゲット言語コード。省略時は `zh`。

---

対応言語コード（50）:
- `zh` 中国語
- `en` 英語
- `ja` 日本語
- `ko` 韓国語
- `es` スペイン語
- `fr` フランス語
- `de` ドイツ語
- `ru` ロシア語
- `it` イタリア語
- `pt` ポルトガル語
- `ar` アラビア語
- `hi` ヒンディー語
- `th` タイ語
- `vi` ベトナム語
- `tr` トルコ語
- `nl` オランダ語
- `pl` ポーランド語
- `id` インドネシア語
- `ms` マレー語
- `fa` ペルシア語
- `uk` ウクライナ語
- `cs` チェコ語
- `sk` スロバキア語
- `hu` ハンガリー語
- `ro` ルーマニア語
- `bg` ブルガリア語
- `hr` クロアチア語
- `sl` スロベニア語
- `sr` セルビア語
- `da` デンマーク語
- `sv` スウェーデン語
- `no` ノルウェー語
- `fi` フィンランド語
- `et` エストニア語
- `lv` ラトビア語
- `lt` リトアニア語
- `el` ギリシャ語
- `he` ヘブライ語
- `bn` ベンガル語
- `ta` タミル語
- `te` テルグ語
- `mr` マラーティー語
- `gu` グジャラート語
- `kn` カンナダ語
- `ml` マラヤーラム語
- `ur` ウルドゥー語
- `sw` スワヒリ語
- `af` アフリカーンス語
- `fil` フィリピン語
- `ca` カタルーニャ語

重要: 翻訳 API が失敗すると原文フォールバックになるため、出力言語が変わらないことがあります。`LLM_API_KEY` とネットワーク/プロキシ設定を確認してください。

---

## 🔁 9. パイプラインとフォールバック戦略

1. 元動画から音声抽出
2. Demucs でボーカル分離
3. Whisper で音声認識
4. Pyannote で話者ダイアライゼーション
5. LLM でセグメント翻訳
6. IndexTTS で一括音声合成
7. クローン失敗時は EdgeTTS へ自動フォールバック
8. タイムラインミックスして最終書き出し

---

## 📦 10. 出力先

既定の出力ディレクトリ:

`backend/storage/outputs/<task_id>/`

主な成果物:
1. `final_<source_video_name>.mp4`
2. `final_<source_video_name>.srt`
3. `final_<source_video_name>_subtitled.mp4`

---

## 🛠️ 11. よくある問題と対策（実ログベース）

### 11.1 ASR ダウンロード失敗（ProxyError / 127.0.0.1:7897）

症状:
`Failed to establish a new connection: [WinError 10061]`

原因:
プロキシ環境変数が有効だがローカルプロキシが未起動。

対策:
1. プロキシクライアントを起動しポート確認。
2. または `HTTP_PROXY` / `HTTPS_PROXY` を削除・コメントアウト。
3. バックエンド再起動。

### 11.2 LLM 翻訳失敗（SSL EOF）

症状:
`SSLEOFError: EOF occurred in violation of protocol`

原因:
ネットワーク/TLS/プロキシの中断。

対策:
1. プロキシと回線状態を確認。
2. 別回線で再実行。
3. 原文フォールバックは仕様上の正常動作。

### 11.3 なぜ中国語指定なのに英語のまま？

根本原因:
翻訳段階が失敗し、原文へフォールバックした。

確認順:
1. ログに `LLM Translation failed` があるか
2. `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` が正しいか
3. ネットワーク/プロキシが正常か

### 11.4 クローン段階で停止、wav が出ない

確認点:
1. `.env` に正しい `INDEXTTS_DIR` があるか
2. `INDEXTTS_DIR/checkpoints/config.yaml` が存在するか
3. バックエンド環境に依存（librosa/soundfile/torch）が揃っているか
4. バックエンドログの IndexTTS サブプロセスエラーを確認

### 11.5 バックエンド窓が `Active code page: 65001` だけ表示

よくある原因:
作業ディレクトリ不正、または環境未アクティブ。

対策:
1. 配布済みワンクリックスクリプトを使用（古い複雑な `start` 連結を避ける）。
2. `_start_backend.bat` を含む正しい構成を確認。

---

## ⚡ 12. 性能・品質のコツ

1. 可能なら CUDA を使う
2. 参照音声は単一話者・クリア・無背景/低背景・5-15秒推奨
3. 長文は分割して安定性向上
4. 一括クローンでモデル再ロード回数を削減
5. VRAM が少ない場合は並列度を下げるか CPU 経路で先に検証

---

## 🔒 13. セキュリティとコンプライアンス（重要）

1. 実秘密情報（`.env`、Token、APIキー）を絶対に公開しない
2. 権限のないユーザーデータ/私的メディアをアップロードしない
3. 本リポジトリは上流モデル重みを再配布しない。利用者が上流ライセンスに従って取得すること
4. IndexTTS2 の公式ライセンス/免責を遵守
5. 音声クローン対象について法的許諾を必ず取得

---

## 🙏 14. 謝辞と上流参照

1. IndexTTS / IndexTTS2 の公式リポジトリと論文
2. Demucs / Whisper / Pyannote / EdgeTTS などの OSS コンポーネント
3. `THIRD_PARTY_NOTICES.md` を参照

---

## ⚠️ 免責事項

本プロジェクトは、合法かつコンプライアンスに沿った研究・エンジニアリング用途のみを対象とします。メディア利用許諾、モデルライセンス、データコンプライアンス、生成物の適法性については、利用者が単独で責任を負います。
