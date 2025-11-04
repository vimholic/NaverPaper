# Standard library imports
import asyncio
import os
import re
from datetime import datetime, timedelta

# Third-party imports
import pytz
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from telegram import Bot

# Local imports
import fetch_url
from config import Config
from database import Database
from models import UrlVisit, CampaignUrl, User
from utils.common import get_random_ua
from utils.logger import setup_logger, get_log_filename

seoul_tz = pytz.timezone('Asia/Seoul')
db = Database()

# 로거 설정
logger = setup_logger(__name__, get_log_filename('get_paper'))


async def naver_login(page, nid, npw, tt, tci):
    await page.goto("https://new-m.pay.naver.com/pcpay")
    if not page.url.startswith("https://nid.naver.com/"):
        logger.info(f"{nid} - 기존 네이버 로그인 정보 이용")
        return True
    try:
        await page.locator("#id").fill(nid)
        await page.locator("#pw").fill(npw)
        await page.locator("#pw").press("Enter")
        await page.wait_for_selector('a:has-text("로그아웃")', state="visible")
        logger.info(f"{nid} - 네이버 로그인 성공")
        return True
    except Exception as e:
        logger.error(f"{nid} - 네이버 로그인 실패 - {e}")
        await page.screenshot(path=f"login_error_{nid}_{datetime.now(seoul_tz).strftime('%Y%m%d_%H%M%S')}.png")
        if tt and tci:
            await send_telegram_message(tt, tci, f"{nid} - 네이버 로그인 실패")
        return False


async def send_telegram_message(token, chat_id, message):
    bot = Bot(token=token)
    await bot.sendMessage(chat_id=chat_id, text=message)


async def process_campaign2_link(page, link, session_db):
    await page.goto(link, wait_until="networkidle")
    html_content = await page.content()
    soup = BeautifulSoup(html_content, "html.parser")

    block_divs = soup.find_all('div', style=re.compile(r'display\s*:\s*block', re.IGNORECASE),
                               class_=lambda x: x != 'dimmed')
    block_div = block_divs[0] if block_divs else None
    match = None
    if '적립돼요' in block_div.text:
        # 포인트 확인
        match = re.search(r"네이버페이 포인트(\d+)원이", block_div.text or "")
        if match:
            point = int(match.group(1))
            await page.locator('a.popup_link >> text=포인트 받기').click()  # 버튼 클릭
            await asyncio.sleep(Config.PAGE_WAIT_SHORT)
            logger.info(f"캠페인 URL: {link} - {point} 포인트 획득!")
    else:
        block_div_text = ' '.join(block_div.text.split())
        logger.info(f"캠페인 URL: {link} - {block_div_text}")
        if "적립 기간이 아닙니다" in block_div.text:
            campaign_url = session_db.query(CampaignUrl).filter_by(url=link).first()
            if campaign_url:
                campaign_url.is_available = False
    await asyncio.sleep(Config.PAGE_WAIT_SHORT)
    return point if match else 0

async def process_campaign_links(page, campaign_links, session_db, nid):
    points = 0

    for link in campaign_links:
        try:
            if link.startswith("https://campaign2"):
                points += await process_campaign2_link(page, link, session_db)
            elif link.startswith("https://s.ppomppu.co.kr"):
                await page.goto(link)
                await page.wait_for_load_state("networkidle")
                redirected_url = page.url
                if redirected_url.startswith("https://campaign2"):
                    points += await process_campaign2_link(page, redirected_url, session_db)
            else:
                await page.goto(link, wait_until="networkidle")
                await asyncio.sleep(Config.PAGE_WAIT_LONG)
                logger.info(f"캠페인 URL: {link} - 방문 완료")
        except Exception as e:
            logger.error(f"캠페인 URL 처리 오류: {link} - {e}")

        # 방문 기록 저장
        existing_visit = session_db.query(UrlVisit).filter_by(url=link, user_id=nid).first()
        if not existing_visit:
            session_db.add(UrlVisit(url=link, user_id=nid, visited_at=datetime.now()))

    return points


async def send_telegram_message_if_needed(tt, tci, nid, campaign_links, points):
    if tt and tci:
        if (not campaign_links or points == 0) and Config.NO_PAPER_ALARM:
            await send_telegram_message(tt, tci, f"{nid} - 더 이상 주울 네이버 폐지가 없습니다.")
        elif campaign_links and points > 0:
            await send_telegram_message(
                tt,
                tci,
                f"{nid} - {points}원(추정) 폐지 줍기 완료. 적립 내역 확인 - https://new-m.pay.naver.com/pointshistory/list?depth2Slug=event"
            )


async def process_account(nid, npw, session_db, tt=None, tci=None):
    nid = nid.strip()
    npw = npw.strip()
    logger.info(f"{nid} - 네이버 폐지 줍기 시작")
    campaign_links = await fetch_url.fetch_naver_campaign_urls(session_db, nid)
    if campaign_links:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            file_path = f"{nid}.json"
            if os.path.exists(file_path):
                context = await browser.new_context(storage_state=file_path, user_agent=get_random_ua())
            else:
                user = session_db.query(User).filter_by(user_id=nid).first()
                storage_state = user.storage_state if user else None
                context = await browser.new_context(storage_state=storage_state, user_agent=get_random_ua())
            page = await context.new_page()
            login = await naver_login(page, nid, npw, tt, tci)
            if login:
                points = await process_campaign_links(page, campaign_links, session_db, nid)
                await send_telegram_message_if_needed(tt, tci, nid, campaign_links, points)
                storage_state = await context.storage_state()
                session_db.merge(User(user_id=nid, storage_state=storage_state, updated_at=datetime.now()))
            await context.close()
    logger.info(f"{nid} - 네이버 폐지 줍기 완료")


async def process_with_telegram(naver_ids, naver_pws, telegram_tokens, telegram_chat_ids, session_db):
    for nid, npw, tt, tci in zip(naver_ids, naver_pws, telegram_tokens, telegram_chat_ids):
        tt = tt.strip()
        tci = tci.strip()
        await process_account(nid, npw, session_db, tt, tci)


async def process_without_telegram(naver_ids, naver_pws, session_db):
    for nid, npw in zip(naver_ids, naver_pws):
        await process_account(nid, npw, session_db)


def delete_old_stuff(session_db):
    current_date = datetime.now()
    campaign_cutoff = current_date - timedelta(days=Config.CAMPAIGN_RETENTION_DAYS)
    try:
        old_urls = session_db.query(CampaignUrl).filter(CampaignUrl.date_added < campaign_cutoff)
        for old_url in old_urls:
            old_visits = session_db.query(UrlVisit).filter_by(url=old_url.url)
            old_visits.delete()
        old_urls.delete()
        logger.info(f"캠페인 URL 정리 완료 ({Config.CAMPAIGN_RETENTION_DAYS}일 이전)")

        session_cutoff = current_date - timedelta(days=Config.USER_SESSION_RETENTION_DAYS)
        deleted_count = session_db.query(User).filter(User.updated_at < session_cutoff).delete()
        logger.info(f"사용자 세션 정리 완료: {deleted_count}개 ({Config.USER_SESSION_RETENTION_DAYS}일 이전)")
    except Exception as e:
        logger.error(f"오래된 데이터 삭제 중 오류 발생 - {e}")


async def main():
    # 설정 검증
    try:
        Config.validate()
        logger.info("설정 검증 완료")
    except ValueError as e:
        logger.error(f"설정 오류: {e}")
        return

    naver_ids = Config.NAVER_IDS
    naver_pws = Config.NAVER_PWS
    telegram_token_txt = Config.TELEGRAM_TOKEN
    telegram_chat_id_txt = Config.TELEGRAM_CHAT_ID

    with db.get_session() as session_db:
        logger.info("캠페인 URL 수집 시작")
        await fetch_url.save_naver_campaign_urls(session_db)
        logger.info("캠페인 URL 수집 종료")
        if telegram_token_txt and telegram_chat_id_txt:
            telegram_tokens = telegram_token_txt.split('|')
            telegram_chat_ids = telegram_chat_id_txt.split('|')
            await process_with_telegram(naver_ids, naver_pws, telegram_tokens, telegram_chat_ids, session_db)
        elif not telegram_token_txt or not telegram_chat_id_txt:
            await process_without_telegram(naver_ids, naver_pws, session_db)
        delete_old_stuff(session_db)
        session_db.commit()


if __name__ == '__main__':
    asyncio.run(main())
