from aiohttp import ClientSession
from urllib.parse import urljoin
import asyncio
from models import UrlVisit, CampaignUrl
from bs4 import BeautifulSoup
import pytz
from datetime import datetime

campaign_urls = set()
seoul_tz = pytz.timezone('Asia/Seoul')


async def fetch(url, session):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Mobile Safari/537.36'}
    async with session.get(url, headers=headers) as response:
        return await response.text(errors="ignore")


async def process_url(url, session, process_func):
    response = await fetch(url, session)
    soup = BeautifulSoup(response, "html.parser")
    await process_func(url, soup, session)


async def process_clien_url(url, soup, session):
    print("클리앙 URL 수집 시작 - " + datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S'))
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
            print(f"{full_link} - {e}")
            continue
        for a_tag in inner_soup.find_all("a", href=True):
            if a_tag["href"].startswith("https://campaign2-api.naver.com") or a_tag["href"].startswith(
                    "https://ofw.adison.co"):
                campaign_urls.add(a_tag["href"])
    added_count = len(campaign_urls) - initial_count
    print(f"클리앙에서 수집된 URL 수: {added_count}")
    print("클리앙 URL 수집 종료 - " + datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S'))


async def process_ppomppu_url(url, soup, session):
    print("뽐뿌 URL 수집 시작 - " + datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S'))
    initial_count = len(campaign_urls)
    base_url = "https://www.ppomppu.co.kr/zboard/zboard.php?"
    naver_links = [a['href'] for a in soup.select('#revolution_main_table td.list_vspace[align="left"] a') if
                   "네이버" in a.text]

    for link in naver_links:
        full_link = urljoin(base_url, link)
        res = await fetch(full_link, session)
        try:
            inner_soup = BeautifulSoup(res, "html.parser")
        except Exception as e:
            print(f"{full_link} - {e}")
            continue
        for a_tag in inner_soup.select(
                'a[href^="https://campaign2-api.naver.com"], a[href^="https://s.ppomppu.co.kr?idno=coupon"]'):
            a_tag_text = a_tag.get_text(strip=True).replace(" ", "")
            if a_tag_text.startswith("https://campaign2-api.naver.com") or a_tag_text.startswith(
                    "https://ofw.adison.co"):
                campaign_urls.add(a_tag_text)
    added_count = len(campaign_urls) - initial_count
    print(f"뽐뿌에서 수집된 URL 수: {added_count}")
    print("뽐뿌 URL 수집 종료 - " + datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S'))


async def process_damoang_url(url, soup, session):
    print("다모앙 URL 수집 시작 - " + datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S'))
    initial_count = len(campaign_urls)
    section = soup.find("section", id='bo_list')
    items = section.find_all('a', class_='da-link-block da-article-link subject-ellipsis', attrs={"href": True})
    naver_links = []
    for item in items:
        onclick_attr = item.get('href')
        if onclick_attr and '네이버' in item.text:
            link = onclick_attr
            naver_links.append(link)

    for link in naver_links:
        res = await fetch(link, session)
        try:
            inner_soup = BeautifulSoup(res, "html.parser")
        except Exception as e:
            print(f"{link} - {e}")
            continue
        for a_tag in inner_soup.find_all("a", href=True):
            if a_tag["href"].startswith("https://campaign2-api.naver.com") or a_tag["href"].startswith(
                    "https://ofw.adison.co"):
                campaign_urls.add(a_tag["href"])
    added_count = len(campaign_urls) - initial_count
    print(f"다모앙에서 수집된 URL 수: {added_count}")
    print("다모앙 URL 수집 종료 - " + datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S'))


async def save_naver_campaign_urls(session_db):
    urls = [
        ("https://www.clien.net/service/board/jirum", process_clien_url),
        ("https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", process_ppomppu_url),
        ("https://damoang.net/economy", process_damoang_url)
    ]
    async with ClientSession() as session:
        for url, process_func in urls:
            try:
                await process_url(url, session, process_func)
            except Exception as e:
                print(f"{url} - {e}")
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
