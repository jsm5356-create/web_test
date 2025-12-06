import streamlit as st
from datetime import datetime, date
import plotly.express as px
import pandas as pd
from utils.github_manager import GithubManager
from utils.rss_crawler import parse_rss_feeds
from utils.ai_analyst import analyze_news_with_gemini

# 페이지 설정
st.set_page_config(
    page_title="나만의 뉴스룸",
    page_icon="📰",
    layout="wide"
)

# 로컬 테스트 모드 확인 (Streamlit Cloud에서는 항상 false)
use_local = False
try:
    use_local_str = st.secrets.get("USE_LOCAL_STORAGE", "false")
    if isinstance(use_local_str, str):
        use_local = use_local_str.lower() == "true"
except:
    use_local = False

if use_local:
    # 로컬 모드: 로컬 파일 시스템 사용 (로컬 개발용)
    try:
        gemini_api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("⚠️ 로컬 모드에서는 GEMINI_API_KEY만 필요합니다.")
        st.stop()
    
    if "github_manager" not in st.session_state:
        st.session_state["github_manager"] = GithubManager(use_local=True)
        st.session_state["gemini_api_key"] = gemini_api_key
        st.info("📁 로컬 파일 시스템 모드로 실행 중입니다. (data/ 폴더 사용)")
else:
    # GitHub 모드 (Streamlit Cloud에서는 항상 이 모드)
    try:
        github_token = st.secrets.get("GITHUB_TOKEN")
        repo_name = st.secrets.get("REPO_NAME")
        gemini_api_key = st.secrets.get("GEMINI_API_KEY")
        
        # 필수 값 확인
        if not github_token:
            raise KeyError("GITHUB_TOKEN")
        if not repo_name:
            raise KeyError("REPO_NAME")
        if not gemini_api_key:
            raise KeyError("GEMINI_API_KEY")
            
    except KeyError as e:
        st.error(f"⚠️ Streamlit Cloud Secrets에 필요한 설정이 없습니다: {e}")
        st.info("**Streamlit Cloud 대시보드에서 다음 Secrets를 추가해주세요:**")
        st.code("""
GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
REPO_NAME = "username/repo-name"
GEMINI_API_KEY = "xxxxxxxxxxxx"
ADMIN_PASSWORD = "your_password"
        """)
        st.info("💡 **설정 방법:** Streamlit Cloud 앱 페이지 → Settings → Secrets → 위 내용을 추가하세요.")
        st.stop()
    
    # GithubManager 초기화
    if "github_manager" not in st.session_state:
        try:
            st.session_state["github_manager"] = GithubManager(github_token, repo_name, use_local=False)
            st.session_state["gemini_api_key"] = gemini_api_key
        except Exception as e:
            st.error(f"GitHub 인증 실패: {e}")
            st.info("💡 GitHub Token과 Repository 이름을 확인해주세요.")
            st.stop()

github_manager = st.session_state["github_manager"]

# 사이드바 메뉴
with st.sidebar:
    page = st.radio(
        "메뉴 선택",
        ["홈 (뉴스룸)", "관리자 대시보드"],
        key="page_selector"
    )
    
    # 관리자 대시보드 접근 제어
    if page == "관리자 대시보드":
        st.divider()
        admin_password = st.text_input(
            "관리자 비밀번호",
            type="password",
            key="admin_password_input"
        )
        
        if admin_password:
            try:
                correct_password = st.secrets.get("ADMIN_PASSWORD", "")
                if admin_password == correct_password:
                    st.session_state["admin_authenticated"] = True
                    st.success("✅ 인증 완료")
                else:
                    st.session_state["admin_authenticated"] = False
                    st.error("❌ 비밀번호가 올바르지 않습니다.")
            except KeyError:
                st.warning("⚠️ ADMIN_PASSWORD가 설정되지 않았습니다.")
                st.session_state["admin_authenticated"] = True  # 비밀번호가 없으면 허용

# 방문자 통계 업데이트 (한 세션당 1회만)
if "visit_counted" not in st.session_state:
    try:
        stats = github_manager.load_json("data/stats.json")
        if not stats:
            stats = {"visits": 0, "last_updated": None}
        
        stats["visits"] = stats.get("visits", 0) + 1
        stats["last_updated"] = datetime.now().isoformat()
        
        # 조용히 저장 (사용자 경험을 위해 에러만 표시)
        github_manager.save_json("data/stats.json", stats, "방문자 통계 업데이트")
        st.session_state["visit_counted"] = True
    except Exception as e:
        # 에러는 조용히 무시 (통계는 중요하지 않음)
        pass


# 홈 화면
if page == "홈 (뉴스룸)":
    st.title("📰 나만의 뉴스룸")
    
    # 날짜 선택
    selected_date = st.date_input(
        "날짜 선택",
        value=date.today(),
        max_value=date.today()
    )
    
    # 뉴스 히스토리 로드
    try:
        news_history = github_manager.load_json("data/news_history.json")
        date_key = selected_date.strftime("%Y-%m-%d")
        
        if date_key in news_history:
            st.markdown("---")
            st.markdown(f"### {selected_date.strftime('%Y년 %m월 %d일')} 뉴스 요약")
            st.markdown(news_history[date_key])
        else:
            st.info(f"{selected_date.strftime('%Y년 %m월 %d일')}의 데이터가 없습니다. 관리자 대시보드에서 데이터를 수집해주세요.")
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")


# 관리자 대시보드
elif page == "관리자 대시보드":
    # 관리자 인증 확인
    if not st.session_state.get("admin_authenticated", False):
        st.title("⚙️ 관리자 대시보드")
        st.warning("⚠️ 사이드바에서 관리자 비밀번호를 입력해주세요.")
        st.stop()
    
    st.title("⚙️ 관리자 대시보드")
    
    tab1, tab2, tab3 = st.tabs(["RSS 관리", "데이터 수집 및 분석", "통계"])
    
    # RSS 관리 탭
    with tab1:
        st.header("📡 RSS 피드 관리")
        
        try:
            feeds = github_manager.load_json("data/feeds.json")
            if not feeds:
                feeds = []
            
            # 현재 RSS 목록 표시
            if feeds:
                st.subheader("등록된 RSS 피드")
                for i, feed_url in enumerate(feeds):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.text(feed_url)
                    with col2:
                        if st.button("삭제", key=f"delete_{i}"):
                            feeds.remove(feed_url)
                            if github_manager.save_json("data/feeds.json", feeds, "RSS 피드 삭제"):
                                st.success("RSS 피드가 삭제되었습니다.")
                                st.rerun()
            else:
                st.info("등록된 RSS 피드가 없습니다.")
            
            st.divider()
            
            # 새 RSS 추가
            st.subheader("새 RSS 피드 추가")
            new_feed = st.text_input("RSS URL 입력", placeholder="https://example.com/rss")
            if st.button("추가"):
                if new_feed and new_feed not in feeds:
                    feeds.append(new_feed)
                    if github_manager.save_json("data/feeds.json", feeds, "RSS 피드 추가"):
                        st.success("RSS 피드가 추가되었습니다.")
                        st.rerun()
                elif new_feed in feeds:
                    st.warning("이미 등록된 RSS 피드입니다.")
                else:
                    st.warning("유효한 URL을 입력해주세요.")
        
        except Exception as e:
            st.error(f"RSS 관리 오류: {e}")
    
    # 데이터 수집 및 분석 탭
    with tab2:
        st.header("🔄 데이터 수집 및 분석")
        
        if st.button("📥 뉴스 수집 및 AI 분석 실행", type="primary"):
            try:
                # RSS 피드 로드
                feeds = github_manager.load_json("data/feeds.json")
                if not feeds:
                    st.warning("등록된 RSS 피드가 없습니다. RSS 관리 탭에서 피드를 추가해주세요.")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 1. RSS 크롤링
                    status_text.text("RSS 피드를 크롤링하는 중...")
                    progress_bar.progress(20)
                    news_list = parse_rss_feeds(feeds)
                    st.success(f"✅ {len(news_list)}개의 뉴스 기사를 수집했습니다.")
                    
                    if news_list:
                        # 2. AI 분석
                        status_text.text("Gemini AI로 뉴스를 분석하는 중... (시간이 걸릴 수 있습니다)")
                        progress_bar.progress(60)
                        
                        analysis_result = analyze_news_with_gemini(news_list, gemini_api_key)
                        
                        progress_bar.progress(90)
                        
                        # 3. 결과 저장
                        status_text.text("결과를 GitHub에 저장하는 중...")
                        news_history = github_manager.load_json("data/news_history.json")
                        if not news_history:
                            news_history = {}
                        
                        today_key = datetime.now().strftime("%Y-%m-%d")
                        news_history[today_key] = analysis_result
                        
                        if github_manager.save_json("data/news_history.json", news_history, f"{today_key} 뉴스 분석 결과 저장"):
                            progress_bar.progress(100)
                            status_text.text("✅ 완료!")
                            st.success("뉴스 수집 및 분석이 완료되었습니다!")
                            st.markdown("---")
                            st.markdown("### 분석 결과 미리보기")
                            st.markdown(analysis_result)
                        else:
                            st.error("저장 중 오류가 발생했습니다.")
                    else:
                        st.warning("수집된 뉴스가 없습니다.")
            
            except Exception as e:
                st.error(f"오류 발생: {e}")
    
    # 통계 탭
    with tab3:
        st.header("📊 통계")
        
        try:
            stats = github_manager.load_json("data/stats.json")
            if stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("총 방문자 수", stats.get("visits", 0))
                with col2:
                    last_updated = stats.get("last_updated")
                    if last_updated:
                        last_date = datetime.fromisoformat(last_updated)
                        st.metric("마지막 업데이트", last_date.strftime("%Y-%m-%d %H:%M"))
                
                # 간단한 차트 (향후 확장 가능)
                if stats.get("visits", 0) > 0:
                    st.subheader("방문 통계")
                    df = pd.DataFrame({
                        "항목": ["총 방문자 수"],
                        "값": [stats.get("visits", 0)]
                    })
                    fig = px.bar(df, x="항목", y="값", title="방문자 통계")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("통계 데이터가 없습니다.")
        except Exception as e:
            st.error(f"통계 로드 오류: {e}")

