#!/usr/bin/env python3
"""
文字起こしモジュール
AmiVoice Cloud API対応

MedicalRecorderと同じAPI設定を使用可能
"""

import requests
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class AmiVoiceTranscriber:
    """AmiVoice Cloud APIクライアント"""

    # エンジン一覧
    ENGINES = {
        "general": "-a-general",      # 汎用
        "medical": "-a-medical",      # 医療
        "business": "-a-business",    # ビジネス
        "call": "-a-call",            # コールセンター（電話向け）
    }

    def __init__(self, api_key: str, engine: str = "call"):
        """
        初期化

        Args:
            api_key: AmiVoice APIキー
            engine: エンジン名 (general, medical, business, call)
        """
        self.api_key = api_key
        self.engine = self.ENGINES.get(engine, engine)
        self.endpoint = "https://acp-api.amivoice.com/v1/recognize"

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        音声ファイルを文字起こし

        Args:
            audio_path: WAVファイルパス

        Returns:
            結果辞書 {
                "success": bool,
                "text": str,          # 文字起こし結果
                "confidence": float,  # 信頼度
                "duration": float,    # 音声時間
                "error": str          # エラーメッセージ（失敗時）
            }
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            return {"success": False, "error": f"ファイルが見つかりません: {audio_path}"}

        # リクエスト準備
        try:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()

            # マルチパートフォームデータ
            files = {
                'a': (audio_path.name, audio_data, 'audio/wav')
            }
            data = {
                'u': self.api_key,
                'd': self.engine,
            }

            print(f"文字起こし中: {audio_path.name} (エンジン: {self.engine})")

            # API呼び出し
            response = requests.post(
                self.endpoint,
                files=files,
                data=data,
                timeout=300  # 5分タイムアウト
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"APIエラー: {response.status_code} - {response.text}"
                }

            # レスポンス解析
            result = response.json()
            return self._parse_response(result)

        except requests.exceptions.Timeout:
            return {"success": False, "error": "タイムアウト: 応答がありませんでした"}
        except Exception as e:
            return {"success": False, "error": f"エラー: {str(e)}"}

    def _parse_response(self, response: dict) -> Dict[str, Any]:
        """AmiVoiceレスポンスを解析"""
        # エラーチェック
        if 'results' not in response:
            error_msg = response.get('message', response.get('text', '不明なエラー'))
            return {"success": False, "error": error_msg}

        # テキスト抽出
        results = response.get('results', [])
        if not results:
            return {"success": True, "text": "", "confidence": 0.0, "duration": 0.0}

        # 全セグメントのテキストを結合
        texts = []
        total_confidence = 0.0
        total_duration = 0.0

        for segment in results:
            tokens = segment.get('tokens', [])
            for token in tokens:
                texts.append(token.get('written', ''))

            total_confidence += segment.get('confidence', 0.0)
            total_duration += (segment.get('endtime', 0) - segment.get('starttime', 0)) / 1000.0

        avg_confidence = total_confidence / len(results) if results else 0.0

        return {
            "success": True,
            "text": ''.join(texts),
            "confidence": avg_confidence,
            "duration": total_duration,
            "raw_response": response  # デバッグ用
        }


class SakuraWhisperTranscriber:
    """さくらのAI (Whisper) クライアント"""

    def __init__(self, token_id: str, secret: str):
        """
        初期化

        Args:
            token_id: さくらのAI トークンID
            secret: さくらのAI シークレット
        """
        self.token_id = token_id
        self.secret = secret
        self.endpoint = "https://api.ai.sakura.ad.jp/v1/audio/transcriptions"

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """音声ファイルを文字起こし"""
        audio_path = Path(audio_path)

        if not audio_path.exists():
            return {"success": False, "error": f"ファイルが見つかりません: {audio_path}"}

        try:
            with open(audio_path, 'rb') as f:
                files = {
                    'file': (audio_path.name, f, 'audio/wav')
                }
                data = {
                    'model': 'whisper-large-v3-turbo',
                    'language': 'ja'
                }

                # Basic認証
                auth = (self.token_id, self.secret)

                print(f"文字起こし中: {audio_path.name} (さくらWhisper)")

                response = requests.post(
                    self.endpoint,
                    files=files,
                    data=data,
                    auth=auth,
                    timeout=300
                )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"APIエラー: {response.status_code} - {response.text}"
                }

            result = response.json()
            return {
                "success": True,
                "text": result.get('text', ''),
                "confidence": 1.0,  # Whisperは信頼度を返さない
                "duration": result.get('duration', 0.0)
            }

        except Exception as e:
            return {"success": False, "error": f"エラー: {str(e)}"}


def save_transcript(text: str, audio_path: str, output_dir: str = "transcripts") -> str:
    """
    文字起こし結果を保存

    Args:
        text: 文字起こしテキスト
        audio_path: 元の音声ファイルパス
        output_dir: 出力ディレクトリ

    Returns:
        保存したファイルパス
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ファイル名生成
    audio_name = Path(audio_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{audio_name}_transcript.md"

    # Markdown形式で保存
    content = f"""# 通話記録

**録音ファイル:** {Path(audio_path).name}
**文字起こし日時:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 内容

{text}

---

*ISO 15189 通話記録 - Tel-Addapter*
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"文字起こし保存: {output_path}")
    return str(output_path)


# テスト用
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("使用方法: python transcriber.py <APIキー> <音声ファイル>")
        print("例: python transcriber.py YOUR_API_KEY recordings/call_20251224.wav")
        sys.exit(1)

    api_key = sys.argv[1]
    audio_file = sys.argv[2]

    # AmiVoice (コールセンターエンジン) でテスト
    transcriber = AmiVoiceTranscriber(api_key, engine="call")
    result = transcriber.transcribe(audio_file)

    if result["success"]:
        print("\n=== 文字起こし結果 ===")
        print(result["text"])
        print(f"\n信頼度: {result['confidence']:.2f}")
        print(f"音声時間: {result['duration']:.1f}秒")

        # 保存
        save_transcript(result["text"], audio_file)
    else:
        print(f"\nエラー: {result['error']}")
