#!/usr/bin/env python3
"""
設定管理モジュール
"""

import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class Config:
    """アプリケーション設定"""

    # AmiVoice設定
    amivoice_api_key: str = ""
    amivoice_engine: str = "call"  # general, medical, business, call

    # さくらのAI設定（代替）
    sakura_token_id: str = ""
    sakura_secret: str = ""

    # 使用する文字起こしAPI
    transcription_provider: str = "amivoice"  # amivoice, sakura

    # GitHub設定
    github_token: str = ""
    github_owner: str = ""
    github_repo: str = ""
    github_branch: str = "main"
    github_path: str = "call_records"

    # 保存オプション
    save_audio_to_github: bool = False
    save_raw_transcript: bool = True

    # 録音設定
    recordings_dir: str = "recordings"
    transcripts_dir: str = "transcripts"
    sample_rate: int = 16000
    audio_device_index: Optional[int] = None

    @classmethod
    def load(cls, config_path: str = "config.json") -> "Config":
        """設定ファイルから読み込み"""
        config_path = Path(config_path)

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)

        # 環境変数から読み込み
        return cls(
            amivoice_api_key=os.getenv("AMIVOICE_API_KEY", ""),
            amivoice_engine=os.getenv("AMIVOICE_ENGINE", "call"),
            sakura_token_id=os.getenv("SAKURA_TOKEN_ID", ""),
            sakura_secret=os.getenv("SAKURA_SECRET", ""),
            transcription_provider=os.getenv("TRANSCRIPTION_PROVIDER", "amivoice"),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            github_owner=os.getenv("GITHUB_OWNER", ""),
            github_repo=os.getenv("GITHUB_REPO", ""),
            github_branch=os.getenv("GITHUB_BRANCH", "main"),
            github_path=os.getenv("GITHUB_PATH", "call_records"),
        )

    def save(self, config_path: str = "config.json"):
        """設定ファイルに保存"""
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        print(f"設定を保存しました: {config_path}")

    def validate(self) -> tuple[bool, list[str]]:
        """設定の検証"""
        errors = []

        # 文字起こしAPI
        if self.transcription_provider == "amivoice":
            if not self.amivoice_api_key:
                errors.append("AmiVoice APIキーが設定されていません")
        elif self.transcription_provider == "sakura":
            if not self.sakura_token_id or not self.sakura_secret:
                errors.append("さくらのAI認証情報が設定されていません")

        # GitHub
        if not self.github_token:
            errors.append("GitHub Tokenが設定されていません")
        if not self.github_owner:
            errors.append("GitHubオーナーが設定されていません")
        if not self.github_repo:
            errors.append("GitHubリポジトリが設定されていません")

        return len(errors) == 0, errors


def create_sample_config():
    """サンプル設定ファイルを作成"""
    config = Config()
    sample_path = "config.sample.json"
    config.save(sample_path)
    print(f"サンプル設定ファイルを作成しました: {sample_path}")
    print("このファイルをconfig.jsonにコピーして、値を設定してください。")


if __name__ == "__main__":
    create_sample_config()
