멋진 아이디어입니다! **Streamlit Cloud + GitHub Repository(JSON Storage) + Gemini API** 조합은 서버 비용 없이 개인화된 뉴스룸을 구축하기에 아주 효율적인 아키텍처입니다.

Cursor AI를 통해 개발하기 쉽도록 **프로젝트 구조**와 **핵심 로직**, 그리고 **Cursor에 입력할 프롬프트 가이드**를 정리해 드립니다.

---

### ⚠️ 핵심 기술적 제약 사항 및 해결책
Streamlit Cloud는 **Read-only(읽기 전용)** 파일 시스템과 유사합니다. 로컬에서처럼 `open('data.json', 'w')`로 파일을 저장하면, 앱이 재부팅될 때 **데이터가 초기화**됩니다.

따라서, **"DB 없이 JSON 저장"**을 구현하려면 **GitHub API를 사용하여 리포지토리의 파일 내용을 직접 갱신(Commit)**하는 코드를 작성해야 합니다.

---

### 1. 프로젝트 구조 (Directory Structure)

Cursor에서 먼저 아래와 같이 폴더와 빈 파일들을 생성해 주세요.

```text
my-newsroom/
├── .gitignore            # Git 무시 파일 목록
├── data/
│   ├── feeds.json        # RSS URL 목록 (초기값: 빈 배열 [])
│   ├── news_history.json # 날짜별 분석된 뉴스 데이터 (초기값: 빈 객체 {})
│   └── stats.json        # 방문자 통계 (초기값: {"visits": 0})
├── utils/
│   ├── github_manager.py # 깃헙 API로 JSON 읽기/쓰기 담당
│   ├── rss_crawler.py    # RSS 파싱 담당
│   └── ai_analyst.py     # Gemini API 호출 담당
├── app.py                # 메인 Streamlit 앱
└── requirements.txt      # 의존성 패키지
```

---

### 2. 사전 준비 사항 (API Key)

1.  **Google Gemini API Key:** [Google AI Studio](https://aistudio.google.com/)에서 발급.
2.  **GitHub Personal Access Token (Classic):** `repo` 권한이 체크된 토큰 발급.

> **⚠️ 테스트 환경용:** 이 프로젝트는 테스트 목적으로 **Streamlit의 비밀번호 입력 필드**를 사용합니다. 앱 실행 시 사이드바에서 API 키를 입력받습니다.
>
> **프로덕션 환경에서는** `st.secrets`를 사용하거나 환경 변수를 활용하는 것을 권장합니다.

**`.gitignore` 파일 생성 (필수):**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Streamlit
.streamlit/secrets.toml

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# 데이터 파일 (선택사항 - GitHub에 저장할 경우 제외)
# data/*.json
```

---

### 3. Cursor AI 개발 가이드 (단계별 프롬프트)

Cursor의 `Composer` (Ctrl+I 또는 Cmd+I) 기능을 사용하여 아래 순서대로 코드를 생성하세요.

#### Step 1: `requirements.txt` 작성
> **Prompt:**
> 파이썬 Streamlit 프로젝트를 위한 requirements.txt를 만들어줘.
> 필요한 라이브러리: streamlit, feedparser, google-generativeai, PyGithub, pandas, plotly, python-dateutil

#### Step 2: GitHub 연동 모듈 (`utils/github_manager.py`) - **가장 중요**
> **Prompt:**
> `utils/github_manager.py`를 작성해줘.
> 1. `PyGithub` 라이브러리를 사용해서 GitHub 리포지토리의 JSON 파일을 읽고 쓰는 `GithubManager` 클래스를 만들어.
> 2. 생성자에서 `github_token`과 `repo_name`을 파라미터로 받아서 인증해.
> 3. `load_json(file_path)`: 파일이 없으면 빈 dict/list를 반환하고, 있으면 내용을 json으로 파싱해서 반환. `st.cache_data` 데코레이터를 사용해서 캐싱해 (ttl=300초).
> 4. `save_json(file_path, data, commit_message)`: 데이터를 json으로 변환 후 리포지토리에 커밋(업데이트)해. 파일이 없으면 생성해. Rate limiting을 고려해서 에러 처리도 추가해.
> 5. `GithubException`, `RateLimitExceededException` 등 예외를 구체적으로 처리해줘.

#### Step 3: RSS 및 AI 모듈 (`utils/rss_crawler.py`, `utils/ai_analyst.py`)
> **Prompt:**
> 1. `utils/rss_crawler.py`: `feedparser`를 사용해서 RSS URL 리스트를 받아 뉴스 제목, 링크, 요약, 날짜를 파싱해서 리스트로 반환하는 함수를 만들어.
> 2. `utils/ai_analyst.py`: `google-generativeai`를 사용해. 뉴스 기사 리스트(텍스트)를 받으면 "오늘의 IT 주요 뉴스 브리핑" 스타일로 마크다운 형식의 요약 보고서를 작성하는 함수를 만들어. 날짜별로 섹션을 나눠줘.

#### Step 4: 메인 앱 UI 및 로직 (`app.py`)
> **Prompt:**
> `app.py`에 Streamlit 메인 로직을 작성해줘.
>
> **기능 요구사항:**
> 1. **사이드바 인증 섹션:** 
>    - GitHub Personal Access Token 입력 (password_input)
>    - GitHub Repository 이름 입력 (text_input, 예: "username/repo-name")
>    - Gemini API Key 입력 (password_input)
>    - 입력된 값들을 `st.session_state`에 저장하고, 모두 입력되면 `GithubManager`를 초기화해.
> 2. **방문자 통계:** 앱이 켜질 때 `stats.json`을 불러와 방문 카운트를 +1 하고 다시 GitHub에 저장해 (세션 상태를 확인해서 새로고침 시 중복 카운트 방지).
> 3. **사이드바 메뉴:** '홈(뉴스룸)'과 '관리자 대시보드' 메뉴 선택.
>
> **홈 화면:**
> - 날짜 선택기(Date Input)를 둬서 날짜를 선택.
> - `news_history.json`에서 해당 날짜의 AI 요약본이 있으면 보여줘. 없으면 "데이터가 없습니다" 출력.
>
> **관리자 대시보드 화면:**
> - **RSS 관리:** `feeds.json`을 읽어와서 리스트로 보여주고, 추가/삭제 할 수 있는 UI. 변경 시 GitHub에 저장.
> - **데이터 수집 및 분석 실행 버튼:** 버튼을 누르면 등록된 RSS를 크롤링하고, Gemini로 분석한 뒤, 오늘 날짜를 Key로 하여 `news_history.json`에 저장(GitHub 커밋). 진행 상황을 progress bar로 표시해.
> - **통계 차트:** `stats.json` 데이터를 시각화 (Plotly 등 사용).

---

### 4. 핵심 코드 미리보기 (참고용)

Cursor가 코드를 생성하겠지만, **GithubManager** 부분은 로직이 까다로울 수 있어 핵심 구현을 미리 드립니다.

**`utils/github_manager.py` 예시:**

```python
import streamlit as st
from github import Github
from github.GithubException import GithubException, RateLimitExceededException
import json
import time

class GithubManager:
    def __init__(self, github_token: str, repo_name: str):
        """
        Args:
            github_token: GitHub Personal Access Token
            repo_name: 리포지토리 이름 (예: "username/repo-name")
        """
        self.token = github_token
        self.repo_name = repo_name
        try:
            self.g = Github(self.token)
            self.repo = self.g.get_repo(self.repo_name)
        except GithubException as e:
            raise ValueError(f"GitHub 인증 실패: {e}")

    @st.cache_data(ttl=300)  # 5분 캐싱
    def load_json(_self, file_path: str):
        """JSON 파일을 GitHub에서 읽어옵니다."""
        try:
            contents = _self.repo.get_contents(file_path)
            return json.loads(contents.decoded_content.decode())
        except GithubException as e:
            if e.status == 404:
                # 파일이 없으면 빈 dict 반환
                return {}
            elif isinstance(e, RateLimitExceededException):
                st.error(f"GitHub API Rate Limit 초과. 잠시 후 다시 시도해주세요.")
                return {}
            else:
                st.error(f"파일 읽기 오류: {e}")
                return {}

    def save_json(self, file_path: str, data: dict, commit_message: str = "Update data"):
        """JSON 파일을 GitHub에 저장합니다."""
        json_str = json.dumps(data, indent=4, ensure_ascii=False)
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
```

**`app.py`의 인증 섹션 예시:**

```python
import streamlit as st
from utils.github_manager import GithubManager

# 사이드바 인증
with st.sidebar:
    st.header("🔐 인증 설정")
    
    github_token = st.text_input(
        "GitHub Personal Access Token",
        type="password",
        value=st.session_state.get("github_token", "")
    )
    
    repo_name = st.text_input(
        "GitHub Repository (예: username/repo-name)",
        value=st.session_state.get("repo_name", "")
    )
    
    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=st.session_state.get("gemini_api_key", "")
    )
    
    # 세션 상태에 저장
    st.session_state["github_token"] = github_token
    st.session_state["repo_name"] = repo_name
    st.session_state["gemini_api_key"] = gemini_api_key
    
    # 모든 값이 입력되었는지 확인
    if github_token and repo_name and gemini_api_key:
        try:
            if "github_manager" not in st.session_state:
                st.session_state["github_manager"] = GithubManager(github_token, repo_name)
            st.success("✅ 인증 완료")
        except Exception as e:
            st.error(f"인증 실패: {e}")
    else:
        st.info("👆 위 필드들을 모두 입력해주세요.")
```

**`app.py`의 통계 처리 부분 주의사항:**
GitHub API에 커밋하는 것은 속도가 느립니다 (1~3초). 따라서 방문할 때마다 커밋하면 사용자 경험이 나빠질 수 있습니다.
*   **권장:** 방문자 수는 화면에만 표시하고, 실제 저장은 '관리자 대시보드'에 들어갔을 때 몰아서 하거나, 비동기로 처리하는 것이 좋지만 Streamlit 단순 구조상 **"앱 로드 시 1회 저장하되, Spinner(로딩바) 없이 조용히 처리"** 하는 방식을 추천합니다.

**Rate Limiting 주의사항:**
- GitHub API: 시간당 5,000 요청 (인증된 사용자)
- Gemini API: 무료 티어는 분당 15 요청, 일일 1,500 요청
- 대량의 RSS 피드를 처리할 때는 배치 처리와 지연 시간(`time.sleep()`)을 고려해야 합니다.

### 5. 초기 데이터 파일 구조

GitHub 리포지토리에 다음 파일들을 미리 생성해두세요:

**`data/feeds.json`:**
```json
[]
```

**`data/news_history.json`:**
```json
{}
```

**`data/stats.json`:**
```json
{
  "visits": 0,
  "last_updated": null
}
```

### 6. 배포 절차

1.  GitHub에 코드를 Push 합니다. (`.gitignore` 파일 포함 확인)
2.  Streamlit Cloud (share.streamlit.io)에 로그인.
3.  New App -> 해당 리포지토리 선택.
4.  Deploy 클릭!
5.  배포 후 앱의 사이드바에서 API 키를 입력하여 사용합니다.

> **참고:** 프로덕션 환경에서는 `st.secrets`를 사용하는 것이 더 안전합니다. Streamlit Cloud 대시보드의 **Secrets** 영역에 다음 형식으로 입력:
> ```toml
> GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
> REPO_NAME = "your_id/repo_name"
> GEMINI_API_KEY = "xxxxxxxxxxxx"
> ```
> 그리고 `app.py`에서 `st.secrets.get("GITHUB_TOKEN")` 형식으로 사용하도록 수정하세요.

### 7. 추가 개선 사항

- **에러 처리:** 네트워크 오류, API 오류 등에 대한 사용자 친화적인 메시지 표시
- **로딩 상태:** 긴 작업(RSS 크롤링, AI 분석) 시 progress bar와 상태 메시지 표시
- **데이터 검증:** JSON 파일 읽기/쓰기 시 데이터 형식 검증
- **캐싱 전략:** 자주 읽는 데이터는 `st.cache_data`로 캐싱하여 GitHub API 호출 최소화

---

이 가이드를 Cursor AI에게 제공하면서 개발을 진행하면 원하시는 "나만의 뉴스룸"을 빠르게 만드실 수 있습니다.