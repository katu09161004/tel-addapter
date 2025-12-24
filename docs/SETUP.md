# Tel-Addapter セットアップガイド

## 概要

ISO 15189対応のための通話記録・文字起こしシステム

## 必要な機材

### ハードウェア

| 機材 | 型番/メーカー | 価格目安 | 購入先 |
|------|--------------|---------|-------|
| Raspberry Pi | Pi 4 または Pi 5 | ¥10,000〜15,000 | 既存使用可 |
| テレホンピックアップ | OM SYSTEM TP8 | ¥1,500〜2,000 | Amazon, ヨドバシ |
| USBオーディオアダプター | 汎用品 | ¥500〜1,500 | Amazon |
| 3.5mm延長ケーブル | 汎用品 | ¥300〜500 | 家電量販店 |

### 接続図

```
固定電話
    │
    │ (耳に当てる)
    ▼
┌──────────────┐
│  TP8 イヤホン  │  ← 耳に入れて受話器を当てる
└──────┬───────┘
       │ 3.5mm
       ▼
┌──────────────────┐
│ USBオーディオ      │
│ アダプター         │
└──────┬───────────┘
       │ USB
       ▼
┌──────────────────┐
│  Raspberry Pi    │
└──────────────────┘
```

## ソフトウェアセットアップ

### 1. Raspberry Pi の準備

```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# 必要なパッケージ
sudo apt install -y python3-pip python3-venv portaudio19-dev

# プロジェクトクローン
git clone https://github.com/YOUR_USERNAME/tel-addapter.git
cd tel-addapter

# Python環境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. オーディオ設定確認

```bash
# USBオーディオデバイス確認
arecord -l

# テスト録音（5秒）
arecord -D plughw:1,0 -f cd -t wav -d 5 test.wav
aplay test.wav
```

### 3. 設定ファイル作成

```bash
# サンプルから設定ファイル作成
cp config.sample.json config.json

# 編集
nano config.json
```

### 設定項目

```json
{
  "amivoice_api_key": "YOUR_AMIVOICE_API_KEY",
  "amivoice_engine": "call",
  "transcription_provider": "amivoice",
  "github_token": "YOUR_GITHUB_TOKEN",
  "github_owner": "YOUR_USERNAME",
  "github_repo": "call-records",
  "github_branch": "main",
  "github_path": "call_records",
  "save_audio_to_github": false,
  "save_raw_transcript": true
}
```

## 使用方法

### 対話モード

```bash
cd src
python main.py
```

### 録音開始

```bash
python main.py --record
# Ctrl+C で停止
```

### ファイル文字起こし

```bash
python main.py --transcribe recordings/call_20251224.wav
```

## AmiVoice エンジン選択

| エンジン | 用途 |
|---------|------|
| call | 電話通話（推奨） |
| general | 汎用 |
| medical | 医療用語 |
| business | ビジネス |

## トラブルシューティング

### USBオーディオが認識されない

```bash
# デバイス確認
lsusb
arecord -l

# 権限確認
sudo usermod -a -G audio $USER
# 再ログイン必要
```

### 録音レベルが低い

```bash
# ミキサー調整
alsamixer
# F6でUSBオーディオ選択、入力レベル調整
```

## ISO 15189 対応

- 通話内容の自動記録
- タイムスタンプ付き保存
- GitHub によるトレーサビリティ確保
- 変更履歴の自動管理
