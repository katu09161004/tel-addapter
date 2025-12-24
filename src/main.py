#!/usr/bin/env python3
"""
Tel-Addapter メインアプリケーション
ISO 15189対応 通話記録システム

使用方法:
    python main.py              # 対話モード
    python main.py --record     # 録音開始
    python main.py --transcribe <file>  # 文字起こし
"""

import argparse
import sys
import time
import signal
from pathlib import Path

from config import Config
from recorder import PhoneRecorder
from transcriber import AmiVoiceTranscriber, SakuraWhisperTranscriber, save_transcript
from github_uploader import GitHubUploader


class TelAddapter:
    """通話記録アプリケーション"""

    def __init__(self, config_path: str = "config.json"):
        self.config = Config.load(config_path)
        self.recorder = None
        self.transcriber = None
        self.uploader = None
        self._running = False

        # 設定検証
        valid, errors = self.config.validate()
        if not valid:
            print("警告: 設定に問題があります:")
            for error in errors:
                print(f"  - {error}")
            print("")

    def setup(self):
        """コンポーネント初期化"""
        # 録音
        self.recorder = PhoneRecorder(self.config.recordings_dir)

        # 文字起こし
        if self.config.transcription_provider == "amivoice":
            self.transcriber = AmiVoiceTranscriber(
                self.config.amivoice_api_key,
                self.config.amivoice_engine
            )
        else:
            self.transcriber = SakuraWhisperTranscriber(
                self.config.sakura_token_id,
                self.config.sakura_secret
            )

        # GitHub
        if self.config.github_token:
            self.uploader = GitHubUploader(
                self.config.github_token,
                self.config.github_owner,
                self.config.github_repo,
                self.config.github_branch,
                self.config.github_path
            )

    def record_and_process(self) -> dict:
        """録音から保存までの一連の処理"""
        result = {
            "success": False,
            "audio_file": None,
            "transcript_file": None,
            "github_url": None,
            "error": None
        }

        # 1. 録音
        print("\n=== 通話録音を開始します ===")
        print("Ctrl+C で録音を停止します\n")

        audio_file = self.recorder.start_recording(self.config.audio_device_index)
        if not audio_file:
            result["error"] = "録音開始に失敗しました"
            return result

        result["audio_file"] = audio_file

        # Ctrl+C待ち
        self._running = True
        try:
            while self._running:
                duration = self.recorder.get_recording_duration()
                print(f"\r録音中... {duration:.0f}秒", end="", flush=True)
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n")

        # 録音停止
        audio_file = self.recorder.stop_recording()

        if not audio_file:
            result["error"] = "録音保存に失敗しました"
            return result

        # 2. 文字起こし
        print("\n=== 文字起こしを開始します ===\n")
        trans_result = self.transcriber.transcribe(audio_file)

        if not trans_result["success"]:
            result["error"] = f"文字起こし失敗: {trans_result['error']}"
            return result

        print(f"\n文字起こし完了 ({trans_result['duration']:.1f}秒)")

        # 3. 保存
        transcript_file = save_transcript(
            trans_result["text"],
            audio_file,
            self.config.transcripts_dir
        )
        result["transcript_file"] = transcript_file

        # 4. GitHub アップロード
        if self.uploader:
            print("\n=== GitHubにアップロード中 ===\n")
            upload_result = self.uploader.upload_call_record(
                transcript_file,
                audio_file,
                self.config.save_audio_to_github
            )

            if upload_result["success"]:
                result["github_url"] = upload_result["results"]["transcript"].get("url")
                print(f"アップロード完了: {result['github_url']}")
            else:
                print(f"アップロード失敗（ローカルには保存済み）")

        result["success"] = True
        return result

    def transcribe_file(self, audio_path: str) -> dict:
        """既存の音声ファイルを文字起こし"""
        result = {
            "success": False,
            "transcript_file": None,
            "github_url": None,
            "error": None
        }

        if not Path(audio_path).exists():
            result["error"] = f"ファイルが見つかりません: {audio_path}"
            return result

        # 文字起こし
        trans_result = self.transcriber.transcribe(audio_path)

        if not trans_result["success"]:
            result["error"] = f"文字起こし失敗: {trans_result['error']}"
            return result

        print(f"\n=== 文字起こし結果 ===\n")
        print(trans_result["text"])
        print(f"\n(信頼度: {trans_result['confidence']:.2f}, 時間: {trans_result['duration']:.1f}秒)")

        # 保存
        transcript_file = save_transcript(
            trans_result["text"],
            audio_path,
            self.config.transcripts_dir
        )
        result["transcript_file"] = transcript_file

        # GitHubアップロード
        if self.uploader:
            upload_result = self.uploader.upload_call_record(
                transcript_file,
                audio_path,
                self.config.save_audio_to_github
            )
            if upload_result["success"]:
                result["github_url"] = upload_result["results"]["transcript"].get("url")

        result["success"] = True
        return result

    def interactive_mode(self):
        """対話モード"""
        print("=" * 50)
        print("  Tel-Addapter - ISO 15189 通話記録システム")
        print("=" * 50)
        print("")
        print("コマンド:")
        print("  r, record    : 録音開始")
        print("  t, transcribe: ファイル文字起こし")
        print("  c, config    : 設定確認")
        print("  q, quit      : 終了")
        print("")

        while True:
            try:
                cmd = input("コマンド> ").strip().lower()

                if cmd in ['q', 'quit', 'exit']:
                    print("終了します")
                    break

                elif cmd in ['r', 'record']:
                    self.record_and_process()

                elif cmd in ['t', 'transcribe']:
                    path = input("音声ファイルパス> ").strip()
                    if path:
                        self.transcribe_file(path)

                elif cmd in ['c', 'config']:
                    print(f"\n設定:")
                    print(f"  文字起こし: {self.config.transcription_provider}")
                    print(f"  エンジン: {self.config.amivoice_engine}")
                    print(f"  GitHub: {self.config.github_owner}/{self.config.github_repo}")
                    print(f"  保存先: {self.config.github_path}")
                    print("")

                elif cmd:
                    print("不明なコマンドです")

            except KeyboardInterrupt:
                print("\n終了します")
                break
            except EOFError:
                break

    def cleanup(self):
        """リソース解放"""
        if self.recorder:
            self.recorder.cleanup()


def main():
    parser = argparse.ArgumentParser(
        description="Tel-Addapter - ISO 15189対応 通話記録システム"
    )
    parser.add_argument(
        "--config", "-c",
        default="config.json",
        help="設定ファイルパス"
    )
    parser.add_argument(
        "--record", "-r",
        action="store_true",
        help="録音モードで起動"
    )
    parser.add_argument(
        "--transcribe", "-t",
        metavar="FILE",
        help="指定ファイルを文字起こし"
    )

    args = parser.parse_args()

    app = TelAddapter(args.config)
    app.setup()

    # シグナルハンドラ
    def signal_handler(sig, frame):
        app._running = False

    signal.signal(signal.SIGINT, signal_handler)

    try:
        if args.transcribe:
            app.transcribe_file(args.transcribe)
        elif args.record:
            app.record_and_process()
        else:
            app.interactive_mode()
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
