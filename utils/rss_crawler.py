import feedparser
from datetime import datetime
from typing import List, Dict
import time


def parse_rss_feeds(rss_urls: List[str]) -> List[Dict]:
    """
    RSS URL 리스트를 받아 뉴스 기사를 파싱합니다.
    
    Args:
        rss_urls: RSS 피드 URL 리스트
        
    Returns:
        뉴스 기사 리스트 (제목, 링크, 요약, 날짜 포함)
    """
    all_news = []
    
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                # 날짜 파싱
                published_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_date = datetime(*entry.published_parsed[:6]).isoformat()
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_date = datetime(*entry.updated_parsed[:6]).isoformat()
                else:
                    published_date = datetime.now().isoformat()
                
                news_item = {
                    'title': entry.get('title', '제목 없음'),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'published': published_date,
                    'source': feed.feed.get('title', url)
                }
                all_news.append(news_item)
            
            # Rate limiting 방지를 위한 짧은 지연
            time.sleep(0.5)
            
        except Exception as e:
            # 에러는 조용히 처리 (Streamlit에서는 필요시 st.warning 사용)
            continue
    
    # 날짜순으로 정렬 (최신순)
    all_news.sort(key=lambda x: x['published'], reverse=True)
    
    return all_news

