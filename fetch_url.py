import asyncio
import pytz
from aiohttp import ClientSession
from urllib.parse import urljoin
from models import UrlVisit, CampaignUrl
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.async_api import async_playwright
from utils.logger import setup_logger, get_log_filename
from utils.common import get_random_ua

campaign_urls = set()
seoul_tz = pytz.timezone('Asia/Seoul')

# 로거 설정
logger = setup_logger(__name__, get_log_filename('fetch_url'))


async def fetch(url, session):
    headers = {'User-Agent': get_random_ua()}
    async with session.get(url, headers=headers) as response:
        return await response.text(errors="ignore")


def _looks_like_cloudflare(html: str) -> bool:
    if not html:
        return True
    lowered = html.lower()
    return (
        'just a moment' in lowered
        or 'cf_chl_' in lowered
        or 'challenge-platform' in lowered
        or 'cloudflare' in lowered
    )


async def fetch_with_playwright(url: str) -> str:
    # Headless 브라우저로 Cloudflare/JS 의존 페이지를 폴백 수집
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=get_random_ua(), locale='ko-KR')
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # 네트워크가 잠잠해질 때까지 대기 (최대 10초)
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            content = await page.content()
            return content
        finally:
            await context.close()
            await browser.close()


async def get_soup(url: str, session: ClientSession) -> BeautifulSoup:
    html = await fetch(url, session)
    if _looks_like_cloudflare(html):
        # CF로 보이면 Playwright 폴백
        try:
            html = await fetch_with_playwright(url)
        except Exception as e:
            logger.error(f"{url} - Playwright 폴백 실패 - {e}")
    try:
        return BeautifulSoup(html or "", "html.parser")
    except Exception as e:
        logger.error(f"{url} - HTML 파싱 실패 - {e}")
        return BeautifulSoup("", "html.parser")


async def process_url(url, session, process_func):
    soup = await get_soup(url, session)
    await process_func(url, soup, session)


async def process_clien_url(url, soup, session):
    logger.info("클리앙 URL 수집 시작")
    initial_count = len(campaign_urls)
    list_subject_links = soup.select('[class="list_item symph-row"]')
    naver_links = []
    for span in list_subject_links:
        a_tag = span.select_one(':-soup-contains("네이버")')
        if a_tag:
            naver_links.append(span['href'])

    for link in naver_links:
        full_link = urljoin(url, link)
        res = await fetch(full_link, session)
        try:
            inner_soup = BeautifulSoup(res, "html.parser")
        except Exception as e:
            logger.error(f"{full_link} - {e}")
            continue
        for a_tag in inner_soup.find_all("a", href=True):
            if a_tag["href"].startswith("https://campaign2.naver.com") or a_tag["href"].startswith(
                    "https://ofw.adison.co"):
                if len(a_tag["href"]) > 40:
                    campaign_urls.add(a_tag["href"])
    added_count = len(campaign_urls) - initial_count
    logger.info(f"클리앙에서 수집된 URL 수: {added_count}")
    logger.info("클리앙 URL 수집 종료")


async def process_ppomppu_url(url, soup, session):
    logger.info("뽐뿌 URL 수집 시작")
    initial_count = len(campaign_urls)
    base_url = "https://m.ppomppu.co.kr"
    naver_links = []
    for a_tag in soup.find_all('a', href=True):
        if '네이버페이' in a_tag.text:
            naver_links.append(a_tag['href'])

    for link in naver_links:
        full_link = urljoin(base_url, link)
        res = await fetch(full_link, session)
        try:
            inner_soup = BeautifulSoup(res, "html.parser")
        except Exception as e:
            logger.error(f"{full_link} - {e}")
            continue
        for a_tag in inner_soup.find_all("a", class_="noeffect", href=True):
            if a_tag["href"].startswith("https://s.ppomppu.co.kr?idno=coupon"):
                if len(a_tag["href"]) > 40:
                    campaign_urls.add(a_tag["href"])
    added_count = len(campaign_urls) - initial_count
    logger.info(f"뽐뿌에서 수집된 URL 수: {added_count}")
    logger.info("뽐뿌 URL 수집 종료")


async def process_damoang_url(url, soup, session):
    logger.info("다모앙 URL 수집 시작")
    initial_count = len(campaign_urls)
    # 목록 페이지에서 '네이버'가 포함된 게시글 링크를 보다 일반적으로 추출
    try:
        anchors = soup.find_all('a', href=True)
    except Exception:
        anchors = []

    naver_links = []
    for a in anchors:
        try:
            text = (a.get_text() or "").strip()
            href = a.get('href')
        except Exception:
            continue
        if not href or not text:
            continue
        if '네이버' in text:
            # 절대 URL 보정
            full_link = urljoin(url, href)
            if full_link not in naver_links:
                naver_links.append(full_link)

    if not naver_links:
        # 기존 선택자 실패 또는 CF 가능성 → Playwright 폴백으로 목록 재시도
        try:
            html = await fetch_with_playwright(url)
            soup_pf = BeautifulSoup(html or "", "html.parser")
            anchors = soup_pf.find_all('a', href=True)
            for a in anchors:
                text = (a.get_text() or "").strip()
                href = a.get('href')
                if href and text and '네이버' in text:
                    full_link = urljoin(url, href)
                    if full_link not in naver_links:
                        naver_links.append(full_link)
        except Exception as e:
            logger.error(f"{url} - 목록 폴백 실패 - {e}")

    # 상세 페이지에서 네이버 캠페인 링크 추출
    for link in naver_links:
        try:
            inner_soup = await get_soup(link, session)
        except Exception as e:
            logger.error(f"{link} - {e}")
            continue
        for a_tag in inner_soup.find_all("a", href=True):
            href = a_tag.get("href")
            if not href:
                continue
            if href.startswith("https://campaign2.naver.com") or href.startswith("https://ofw.adison.co"):
                if len(href) > 40:
                    campaign_urls.add(href)
    added_count = len(campaign_urls) - initial_count
    logger.info(f"다모앙에서 수집된 URL 수: {added_count}")
    logger.info("다모앙 URL 수집 종료")


async def save_naver_campaign_urls(session_db):
    urls = [
        ("https://www.clien.net/service/board/jirum", process_clien_url),
        ("https://m.ppomppu.co.kr/new/bbs_list.php?id=coupon&extref=1", process_ppomppu_url),
        ("https://damoang.net/economy", process_damoang_url)
    ]
    async with ClientSession() as session:
        for url, process_func in urls:
            try:
                await process_url(url, session, process_func)
            except Exception as e:
                logger.error(f"{url} - {e}")
    for link in campaign_urls:
        existing_url = session_db.query(CampaignUrl).filter_by(url=link).first()
        if not existing_url:
            session_db.add(CampaignUrl(url=link))


async def fetch_naver_campaign_urls(session_db, nid):
    campaign_links = set()
    for link in campaign_urls:
        available_url = session_db.query(CampaignUrl).filter_by(url=link, is_available=True).first()
        if available_url:
            existing_visit = session_db.query(UrlVisit).filter_by(url=link, user_id=nid).first()
            if not existing_visit:
                campaign_links.add(link)
    return campaign_links


if __name__ == '__main__':
    from database import Database

    db = Database()
    with db.get_session() as session_db:
        asyncio.run(save_naver_campaign_urls(session_db))
        session_db.commit()
