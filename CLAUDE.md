# Tel-Addapter プロジェクト

**作成者:** Katsuyoshi Fujita（医療機関 検査科技師長）
**作成日:** 2025-12-24
**目的:** ISO 15189対応のための通話記録・文字起こしシステム

---

## プロジェクト概要

医療機関のISO 15189認定対応として、検査科での通話内容を記録し、文字起こしを行うシステム。

### 主要機能
1. 電話通話の録音（Raspberry Pi + 電話カップラー）
2. AmiVoice / さくらWhisper による文字起こし
3. GitHub への自動保存（トレーサビリティ確保）
4. ISO 15189準拠の記録管理

---

## システム構成

```
固定電話 → TP8テレホンピックアップ → USBオーディオ → Raspberry Pi
                                                         │
                                         ┌───────────────┘
                                         ▼
                                    録音(WAV)
                                         │
                                         ▼
                                   文字起こし(AmiVoice)
                                         │
                                         ▼
                                   GitHub保存
```

---

## 技術スタック

- **言語:** Python 3
- **ハードウェア:** Raspberry Pi + TP8 + USBオーディオ
- **文字起こしAPI:**
  - AmiVoice Cloud（コールセンター/医療エンジン）
  - さくらのAI Whisper（代替）
- **クラウド保存:** GitHub API

---

## ディレクトリ構成

```
tel-addapter/
├── CLAUDE.md           # プロジェクト情報
├── requirements.txt    # Python依存関係
├── config.sample.json  # 設定サンプル
├── src/
│   ├── main.py         # メインアプリケーション
│   ├── recorder.py     # 録音モジュール
│   ├── transcriber.py  # 文字起こしモジュール
│   ├── github_uploader.py  # GitHubアップロード
│   └── config.py       # 設定管理
├── docs/
│   ├── SETUP.md        # セットアップガイド
│   └── HARDWARE.md     # ハードウェア購入ガイド
├── recordings/         # 録音ファイル（.gitignore）
└── transcripts/        # 文字起こし結果（.gitignore）
```

---

## クイックスタート

```bash
# 依存関係インストール
pip install -r requirements.txt

# 設定ファイル作成
cp config.sample.json config.json
# config.json を編集してAPIキーを設定

# 起動
cd src
python main.py
```

---

## 関連プロジェクト

- MedicalRecorder: iOS/watchOS 音声録音・文字起こしアプリ
  - パス: `/Users/mars/MedicalRecorder`
  - 同じ文字起こしAPI設定を共有可能

---

## ISO 15189 対応ポイント

- 通話内容の自動記録・タイムスタンプ
- GitHub によるバージョン管理・変更履歴
- 検査依頼・結果報告のコミュニケーション証跡
- 記録の長期保管・検索可能性

---

*このプロジェクトは医療機関のISO 15189認定対応を目的としています。*
