import asyncio
from aiohttp import ClientSession
from lxml import html
from urllib.parse import urljoin
from database import VisitedUrl, get_session
from datetime import datetime, timedelta

visited_urls = set()
campaign_links = []


async def fetch(url, session):
    async with session.get(url) as response:
        return await response.text()


async def process_url(url, session, session_db, process_func):
    response = await fetch(url, session)
    tree = html.fromstring(response)
    await process_func(url, tree, session, session_db)


async def process_clien_url(url, tree, session, session_db):
    # Find all span elements with class 'list_subject' and get 'a' tags
    list_subject_links = tree.xpath('//span[@class="list_subject"]')
    naver_links = []
    for span in list_subject_links:
        a_tag = span.xpath('.//a[contains(text(), "네이버")]/@href')
        if a_tag:
            naver_links.extend(a_tag)

    # Check each Naver link
    for link in naver_links:
        full_link = urljoin(url, link)
        if full_link in visited_urls:
            continue  # Skip already visited links

        res = await fetch(full_link, session)
        inner_tree = html.fromstring(res)

        # Find all links that start with the campaign URL
        for a_tag in inner_tree.xpath('//a[starts-with(@href, "https://campaign2-api.naver.com")]/@href'):
            campaign_links.append(a_tag)

        # Add the visited link to the set and database
        visited_urls.add(full_link)
        session_db.add(VisitedUrl(url=full_link))


async def process_ppomppu_url(url, tree, session, session_db):
    naver_links = tree.xpath(
        '//*[@id="revolution_main_table"]//td[@class="list_vspace" and @align="left"]//a[contains(., "네이버")]/@href')
    base_url = "https://www.ppomppu.co.kr/zboard/zboard.php?"
    # Check each Naver link
    for link in naver_links:
        full_link = urljoin(base_url, link)
        if full_link in visited_urls:
            continue  # Skip already visited links

        res = await fetch(full_link, session)
        inner_tree = html.fromstring(res)

        # Find all links that start with the campaign URL
        for a_tag in inner_tree.xpath(
                '//a[starts-with(@href, "https://campaign2-api.naver.com") or starts-with(@href, "https://ofw.adison.co")]/@href'):
            campaign_links.append(a_tag)

        # Add the visited link to the set and database
        visited_urls.add(full_link)
        session_db.add(VisitedUrl(url=full_link))


def delete_old_urls():
    # Get the current date
    current_date = datetime.now()

    # Calculate the date 30 days ago
    n_days_ago = current_date - timedelta(days=60)

    # Get a session from the database
    session_db = get_session()

    # Find URLs that were added more than 30 days ago
    old_urls = session_db.query(VisitedUrl).filter(VisitedUrl.date_added < n_days_ago)

    # Delete the old URLs
    old_urls.delete()

    # Commit the changes
    session_db.commit()


async def find_naver_campaign_links():
    urls = [
        ("https://www.clien.net/service/board/jirum", process_clien_url),
        ("https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", process_ppomppu_url)
    ]

    # Get a session from the database
    session_db = get_session()

    # Delete URLs that were added more than 30 days ago
    delete_old_urls()

    # Read visited URLs from database
    visited_urls.update(url.url for url in session_db.query(VisitedUrl).all())

    async with ClientSession() as session:
        # Send a request to the base URL
        for url, process_func in urls:
            await process_url(url, session, session_db, process_func)

    # Commit the changes and close the session
    session_db.commit()
    session_db.close()

    return campaign_links


if __name__ == '__main__':
    asyncio.run(find_naver_campaign_links())
