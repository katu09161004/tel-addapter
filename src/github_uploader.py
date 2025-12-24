#!/usr/bin/env python3
"""
GitHub アップロードモジュール
ISO 15189 トレーサビリティ用

MedicalRecorderと同じGitHub設定を使用可能
"""

import requests
import base64
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class GitHubUploader:
    """GitHub APIクライアント"""

    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        branch: str = "main",
        base_path: str = "call_records"
    ):
        """
        初期化

        Args:
            token: GitHub Personal Access Token
            owner: リポジトリオーナー
            repo: リポジトリ名
            branch: ブランチ名
            base_path: 保存先パス
        """
        self.token = token
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.base_path = base_path
        self.api_base = "https://api.github.com"

    def _headers(self) -> dict:
        """APIヘッダー"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

    def upload_file(
        self,
        file_path: str,
        remote_path: Optional[str] = None,
        commit_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ファイルをGitHubにアップロード

        Args:
            file_path: ローカルファイルパス
            remote_path: GitHub上のパス（省略時は自動生成）
            commit_message: コミットメッセージ

        Returns:
            結果辞書
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return {"success": False, "error": f"ファイルが見つかりません: {file_path}"}

        # リモートパス生成
        if remote_path is None:
            timestamp = datetime.now().strftime("%Y/%m")
            remote_path = f"{self.base_path}/{timestamp}/{file_path.name}"

        # コミットメッセージ
        if commit_message is None:
            commit_message = f"通話記録追加: {file_path.name}"

        try:
            # ファイル読み込み・Base64エンコード
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')

            # 既存ファイルのSHA取得（更新の場合必要）
            sha = self._get_file_sha(remote_path)

            # アップロード
            url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{remote_path}"

            payload = {
                "message": commit_message,
                "content": content,
                "branch": self.branch
            }

            if sha:
                payload["sha"] = sha

            response = requests.put(url, headers=self._headers(), json=payload)

            if response.status_code in [200, 201]:
                result = response.json()
                print(f"アップロード成功: {remote_path}")
                return {
                    "success": True,
                    "url": result.get("content", {}).get("html_url", ""),
                    "path": remote_path
                }
            else:
                return {
                    "success": False,
                    "error": f"APIエラー: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {"success": False, "error": f"エラー: {str(e)}"}

    def _get_file_sha(self, path: str) -> Optional[str]:
        """既存ファイルのSHAを取得"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{path}"
        params = {"ref": self.branch}

        try:
            response = requests.get(url, headers=self._headers(), params=params)
            if response.status_code == 200:
                return response.json().get("sha")
        except:
            pass
        return None

    def upload_call_record(
        self,
        transcript_path: str,
        audio_path: Optional[str] = None,
        save_audio: bool = False
    ) -> Dict[str, Any]:
        """
        通話記録をアップロード

        Args:
            transcript_path: 文字起こしファイルパス
            audio_path: 音声ファイルパス（オプション）
            save_audio: 音声ファイルも保存するか

        Returns:
            結果辞書
        """
        results = {"transcript": None, "audio": None}

        # 文字起こしアップロード
        result = self.upload_file(transcript_path)
        results["transcript"] = result

        if not result["success"]:
            return {"success": False, "results": results}

        # 音声ファイルアップロード（オプション）
        if save_audio and audio_path:
            timestamp = datetime.now().strftime("%Y/%m")
            audio_remote = f"{self.base_path}/{timestamp}/audio/{Path(audio_path).name}"
            result = self.upload_file(audio_path, audio_remote)
            results["audio"] = result

        return {"success": True, "results": results}


# テスト用
if __name__ == "__main__":
    import sys

    print("GitHubアップローダーテスト")
    print("=" * 40)
    print("環境変数または設定ファイルからGitHub設定を読み込んでください。")
    print("")
    print("必要な設定:")
    print("  - GITHUB_TOKEN: Personal Access Token")
    print("  - GITHUB_OWNER: リポジトリオーナー")
    print("  - GITHUB_REPO: リポジトリ名")
