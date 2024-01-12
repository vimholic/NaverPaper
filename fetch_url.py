from aiohttp import ClientSession
from lxml import html
from urllib.parse import urljoin
from database import CampaignUrl, UrlVisit
from datetime import datetime, timedelta

campaign_urls = set()


async def fetch(url, session):
    async with session.get(url) as response:
        return await response.text(errors="ignore")


async def process_url(url, session, process_func):
    response = await fetch(url, session)
    tree = html.fromstring(response)
    await process_func(url, tree, session)


async def process_clien_url(url, tree, session):
    list_subject_links = tree.xpath('//span[@class="list_subject"]')
    naver_links = []
    for span in list_subject_links:
        a_tag = span.xpath('.//a[contains(text(), "네이버")]/@href')
        if a_tag:
            naver_links.extend(a_tag)

    for link in naver_links:
        full_link = urljoin(url, link)
        res = await fetch(full_link, session)
        try:
            inner_tree = html.fromstring(res)
        except Exception as e:
            print(f"{full_link} - {e}")
            continue

        for a_tag in inner_tree.xpath(
                '//a[starts-with(@href, "https://campaign2-api.naver.com")]/@href'):
            campaign_urls.add(a_tag)


async def process_ppomppu_url(url, tree, session):
    naver_links = tree.xpath(
        '//*[@id="revolution_main_table"]//td[@class="list_vspace" and @align="left"]//a[contains(., "네이버")]/@href')
    base_url = "https://www.ppomppu.co.kr/zboard/zboard.php?"
    for link in naver_links:
        full_link = urljoin(base_url, link)
        res = await fetch(full_link, session)
        try:
            inner_tree = html.fromstring(res)
        except Exception as e:
            print(f"{full_link} - {e}")
            continue
        for a_tag in inner_tree.xpath(
                '//a[starts-with(@href, "https://campaign2-api.naver.com")]/@href'):
            campaign_urls.add(a_tag)


def delete_old_urls(session_db):
    current_date = datetime.now()
    n_days_ago = current_date - timedelta(days=60)
    old_urls = session_db.query(CampaignUrl).filter(CampaignUrl.date_added < n_days_ago)
    for old_url in old_urls:
        old_visits = session_db.query(UrlVisit).filter_by(url=old_url.url)
        old_visits.delete()
    old_urls.delete()


async def save_naver_campaign_urls(session_db):
    urls = [
        ("https://www.clien.net/service/board/jirum", process_clien_url),
        ("https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", process_ppomppu_url)
    ]
    delete_old_urls(session_db)
    async with ClientSession() as session:
        for url, process_func in urls:
            await process_url(url, session, process_func)
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
