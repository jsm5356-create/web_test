import streamlit as st
from github import Github
from github.GithubException import GithubException, RateLimitExceededException
from typing import Union
import json
import os
import time


class GithubManager:
    def __init__(self, github_token: str = None, repo_name: str = None, use_local: bool = False):
        """
        Args:
            github_token: GitHub Personal Access Token (로컬 모드일 때는 None)
            repo_name: 리포지토리 이름 (예: "username/repo-name", 로컬 모드일 때는 None)
            use_local: 로컬 파일 시스템 사용 여부
        """
        self.use_local = use_local
        
        if use_local:
            # 로컬 모드: data/ 폴더 사용
            self.data_dir = "data"
            os.makedirs(self.data_dir, exist_ok=True)
        else:
            # GitHub 모드
            if not github_token or not repo_name:
                raise ValueError("GitHub 모드를 사용하려면 github_token과 repo_name이 필요합니다.")
            self.token = github_token
            self.repo_name = repo_name
            try:
                self.g = Github(self.token)
                self.repo = self.g.get_repo(self.repo_name)
            except GithubException as e:
                raise ValueError(f"GitHub 인증 실패: {e}")

    def load_json(self, file_path: str):
        """JSON 파일을 읽어옵니다. (로컬 또는 GitHub)"""
        if self.use_local:
            # 로컬 모드: 파일 시스템에서 읽기
            local_path = os.path.join(self.data_dir, os.path.basename(file_path))
            if os.path.exists(local_path):
                try:
                    with open(local_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    st.error(f"JSON 파싱 오류: {local_path}")
                    if "feeds.json" in file_path:
                        return []
                    return {}
            else:
                # 파일이 없으면 기본값 반환
                if "feeds.json" in file_path:
                    return []
                return {}
        else:
            # GitHub 모드
            try:
                contents = self.repo.get_contents(file_path)
                return json.loads(contents.decoded_content.decode())
            except GithubException as e:
                if e.status == 404:
                    # 파일이 없으면 파일 경로에 따라 적절한 기본값 반환
                    if "feeds.json" in file_path:
                        return []  # feeds.json은 배열
                    else:
                        return {}  # 나머지는 객체
                elif isinstance(e, RateLimitExceededException):
                    st.error("GitHub API Rate Limit 초과. 잠시 후 다시 시도해주세요.")
                    if "feeds.json" in file_path:
                        return []
                    return {}
                else:
                    st.error(f"파일 읽기 오류: {e}")
                    if "feeds.json" in file_path:
                        return []
                    return {}

    def save_json(self, file_path: str, data: Union[dict, list], commit_message: str = "Update data"):
        """JSON 파일을 저장합니다. (로컬 또는 GitHub)"""
        json_str = json.dumps(data, indent=4, ensure_ascii=False)
        
        if self.use_local:
            # 로컬 모드: 파일 시스템에 저장
            local_path = os.path.join(self.data_dir, os.path.basename(file_path))
            try:
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                return True
            except Exception as e:
                st.error(f"파일 저장 오류: {e}")
                return False
        else:
            # GitHub 모드
            try:
                # 파일이 이미 존재하면 업데이트
                contents = self.repo.get_contents(file_path)
                self.repo.update_file(contents.path, commit_message, json_str, contents.sha)
                return True
            except GithubException as e:
                if e.status == 404:
                    # 파일이 없으면 생성
                    try:
                        self.repo.create_file(file_path, commit_message, json_str)
                        return True
                    except RateLimitExceededException:
                        st.error("GitHub API Rate Limit 초과. 잠시 후 다시 시도해주세요.")
                        return False
                elif isinstance(e, RateLimitExceededException):
                    st.error("GitHub API Rate Limit 초과. 잠시 후 다시 시도해주세요.")
                    return False
                else:
                    st.error(f"파일 저장 오류: {e}")
                    return False

