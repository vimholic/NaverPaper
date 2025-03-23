import os
import asyncio
import pytz
import fetch_url
import re
import random
from dotenv import load_dotenv
from telegram import Bot
from datetime import datetime, timedelta
from database import Database
from models import UrlVisit, CampaignUrl, User
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

load_dotenv()
seoul_tz = pytz.timezone('Asia/Seoul')
db = Database()


def get_ua():
    uastrings = [
        "Mozilla/5.0 (Linux; Android 12; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.61 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.153 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 10; M2006C3LG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.97 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/19.0 Chrome/102.0.5005.125 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/103.0.5060.63 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; Lenovo TB-J606F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 Safari/537.36",
    ]
    return random.choice(uastrings)


async def naver_login(page, nid, npw, tt, tci):
    await page.goto("https://new-m.pay.naver.com/pcpay")
    if not page.url.startswith("https://nid.naver.com/"):
        print(f"{nid} - 기존 네이버 로그인 정보 이용 - {datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    try:
        await page.locator("#id").fill(nid)
        await page.locator("#pw").fill(npw)
        await page.locator("#pw").press("Enter")
        await page.wait_for_selector('a:has-text("로그아웃")', state="visible")
        print(f"{nid} - 네이버 로그인 성공 - {datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        print(f"{nid} - 네이버 로그인 실패 - {e} - {datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')}")
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
            await asyncio.sleep(3)  # 3초 대기
            print(f"캠페인 URL: {link} - {point} 포인트 획득! - {datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        block_div_text = ' '.join(block_div.text.split())
        print(f"캠페인 URL: {link} - {block_div_text} - {datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')}")
        if "적립 기간이 아닙니다" in block_div.text:
            campaign_url = session_db.query(CampaignUrl).filter_by(url=link).first()
            if campaign_url:
                campaign_url.is_available = False
    await asyncio.sleep(3)
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
                await asyncio.sleep(5)
                print(f"캠페인 URL: {link} - 방문 완료 - {datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"캠페인 URL 처리 오류: {link} - {e}")

        # 방문 기록 저장
        existing_visit = session_db.query(UrlVisit).filter_by(url=link, user_id=nid).first()
        if not existing_visit:
            session_db.add(UrlVisit(url=link, user_id=nid, visited_at=datetime.now()))

    return points


async def send_telegram_message_if_needed(tt, tci, nid, campaign_links, points):
    no_paper_alarm = os.environ.get("NO_PAPER_ALARM")
    if tt and tci:
        if (not campaign_links or points == 0) and no_paper_alarm == "True":
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
    print(f"{nid} - 네이버 폐지 줍기 시작 - {datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')}")
    campaign_links = await fetch_url.fetch_naver_campaign_urls(session_db, nid)
    if campaign_links:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            file_path = f"{nid}.json"
            if os.path.exists(file_path):
                context = await browser.new_context(storage_state=file_path, user_agent=get_ua())
            else:
                user = session_db.query(User).filter_by(user_id=nid).first()
                storage_state = user.storage_state if user else None
                context = await browser.new_context(storage_state=storage_state, user_agent=get_ua())
            page = await context.new_page()
            login = await naver_login(page, nid, npw, tt, tci)
            if login:
                points = await process_campaign_links(page, campaign_links, session_db, nid)
                await send_telegram_message_if_needed(tt, tci, nid, campaign_links, points)
                storage_state = await context.storage_state()
                session_db.merge(User(user_id=nid, storage_state=storage_state, updated_at=datetime.now()))
            await context.close()
    print(f"{nid} - 네이버 폐지 줍기 완료 - {datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')}")


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
    sixty_days_ago = current_date - timedelta(days=60)
    try:
        old_urls = session_db.query(CampaignUrl).filter(CampaignUrl.date_added < sixty_days_ago)
        for old_url in old_urls:
            old_visits = session_db.query(UrlVisit).filter_by(url=old_url.url)
            old_visits.delete()
        old_urls.delete()
        seven_days_ago = current_date - timedelta(days=7)
        session_db.query(User).filter(User.updated_at < seven_days_ago).delete()
    except Exception as e:
        print(f"오래된 데이터 삭제 중 오류 발생 - {e}")


async def main():
    naver_ids = os.environ.get("NAVER_ID").split('|')
    naver_pws = os.environ.get("NAVER_PW").split('|')
    telegram_token_txt = os.environ.get("TELEGRAM_TOKEN")
    telegram_chat_id_txt = os.environ.get("TELEGRAM_CHAT_ID")
    with db.get_session() as session_db:
        print("캠페인 URL 수집 시작 - " + datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S'))
        await fetch_url.save_naver_campaign_urls(session_db)
        print("캠페인 URL 수집 종료 - " + datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S'))
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
