#!/usr/bin/env python3
"""
電話録音モジュール
Raspberry Pi + USBオーディオアダプター用

使用方法:
    recorder = PhoneRecorder()
    recorder.start_recording()
    # ... 通話中 ...
    recorder.stop_recording()
"""

import pyaudio
import wave
import threading
import os
from datetime import datetime
from pathlib import Path


class PhoneRecorder:
    """電話通話録音クラス"""

    def __init__(self, output_dir: str = "recordings"):
        # 録音設定
        self.format = pyaudio.paInt16
        self.channels = 1  # モノラル
        self.sample_rate = 16000  # 16kHz (AmiVoice推奨)
        self.chunk_size = 1024

        # 出力ディレクトリ
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 録音状態
        self.is_recording = False
        self.frames = []
        self.current_file = None
        self.record_thread = None

        # PyAudio初期化
        self.audio = pyaudio.PyAudio()
        self.stream = None

        # デバイス情報を表示
        self._show_audio_devices()

    def _show_audio_devices(self):
        """利用可能なオーディオデバイスを表示"""
        print("=== 利用可能なオーディオデバイス ===")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  [{i}] {info['name']} (入力: {info['maxInputChannels']}ch)")
        print("=" * 40)

    def get_usb_audio_device(self) -> int:
        """USBオーディオデバイスのインデックスを取得"""
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            name = info['name'].lower()
            # USBオーディオデバイスを検索
            if info['maxInputChannels'] > 0 and ('usb' in name or 'audio' in name):
                print(f"USBオーディオデバイス検出: [{i}] {info['name']}")
                return i
        # 見つからない場合はデフォルト
        print("USBオーディオデバイスが見つかりません。デフォルトデバイスを使用します。")
        return None

    def start_recording(self, device_index: int = None) -> str:
        """録音開始"""
        if self.is_recording:
            print("既に録音中です")
            return None

        # デバイスインデックス
        if device_index is None:
            device_index = self.get_usb_audio_device()

        # ファイル名生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = self.output_dir / f"call_{timestamp}.wav"

        # フレームをクリア
        self.frames = []

        # ストリームを開く
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            print(f"オーディオストリームを開けませんでした: {e}")
            return None

        self.is_recording = True

        # 録音スレッド開始
        self.record_thread = threading.Thread(target=self._record_loop)
        self.record_thread.start()

        print(f"録音開始: {self.current_file}")
        return str(self.current_file)

    def _record_loop(self):
        """録音ループ（別スレッドで実行）"""
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f"録音エラー: {e}")
                break

    def stop_recording(self) -> str:
        """録音停止"""
        if not self.is_recording:
            print("録音中ではありません")
            return None

        self.is_recording = False

        # スレッド終了待ち
        if self.record_thread:
            self.record_thread.join(timeout=2.0)

        # ストリームを閉じる
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # WAVファイル保存
        if self.frames and self.current_file:
            self._save_wav()
            print(f"録音完了: {self.current_file}")
            return str(self.current_file)

        return None

    def _save_wav(self):
        """WAVファイルとして保存"""
        with wave.open(str(self.current_file), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))

    def get_recording_duration(self) -> float:
        """現在の録音時間（秒）を取得"""
        if not self.frames:
            return 0.0
        total_samples = len(self.frames) * self.chunk_size
        return total_samples / self.sample_rate

    def cleanup(self):
        """リソース解放"""
        if self.is_recording:
            self.stop_recording()
        self.audio.terminate()


# テスト用
if __name__ == "__main__":
    import time

    recorder = PhoneRecorder()

    print("\n5秒間の録音テストを開始します...")
    print("マイクに向かって話してください。\n")

    filepath = recorder.start_recording()

    if filepath:
        for i in range(5, 0, -1):
            print(f"  残り {i} 秒...")
            time.sleep(1)

        recorder.stop_recording()
        print(f"\n録音ファイル: {filepath}")
        print(f"録音時間: {recorder.get_recording_duration():.1f} 秒")

    recorder.cleanup()
