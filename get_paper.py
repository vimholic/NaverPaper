import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot
import fetch_url
from datetime import datetime
from database import UrlVisit, CampaignUrl, get_session
from playwright.async_api import async_playwright
from pathlib import Path

load_dotenv()


async def naver_login(page, nid, npw, tt, tci):
    await page.goto("https://new-m.pay.naver.com/pcpay")
    if not page.url.startswith("https://nid.naver.com/"):
        return True
    try:
        await page.locator("#id").fill(nid)
        await page.locator("#pw").fill(npw)
        await page.locator('button[type="submit"].btn_login').click()
        await page.wait_for_selector('a:has-text("로그아웃")', state="visible")
        print(f"{nid} - 네이버 로그인 성공 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        print(f"{nid} - 네이버 로그인 실패 - {e} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await page.screenshot(path=f"login_error_{nid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        if tt and tci:
            await send_telegram_message(tt, tci, f"{nid} - 네이버 로그인 실패")
        return False


async def send_telegram_message(token, chat_id, message):
    bot = Bot(token=token)
    await bot.sendMessage(chat_id=chat_id, text=message)


async def process_campaign_links(page, campaign_links, session_db, nid):
    result_text = None

    async def dialog_handler(dialog):
        nonlocal result_text
        result_text = dialog.message
        await dialog.dismiss()

    page.on("dialog", dialog_handler)
    for link in campaign_links:
        try:
            await page.goto(link)
            if result_text:
                print(f"캠페인 URL: {link} - {result_text} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                if "적립 기간이 아닙니다" in result_text:
                    campaign_url = session_db.query(CampaignUrl).filter_by(url=link).first()
                    if campaign_url:
                        campaign_url.is_available = False
            existing_visit = session_db.query(UrlVisit).filter_by(url=link, user_id=nid).first()
            if not existing_visit:
                session_db.add(UrlVisit(url=link, user_id=nid, visited_at=datetime.now()))
            await asyncio.sleep(5)
        except Exception as e:
            print(f"캠페인 URL 처리 오류: {link} - {e}")


async def send_telegram_message_if_needed(tt, tci, nid, campaign_links):
    no_paper_alarm = os.environ.get("NO_PAPER_ALARM")
    if tt and tci:
        if not campaign_links and no_paper_alarm == "True":
            await send_telegram_message(tt, tci, f"{nid} - 더 이상 주울 네이버 폐지가 없습니다.")
        elif campaign_links:
            await send_telegram_message(
                tt,
                tci,
                f"{nid} - 모든 네이버 폐지 줍기를 완료했습니다. 적립 내역 확인 - https://new-m.pay.naver.com/pointshistory/list?depth2Slug=event"
            )


async def process_account(nid, npw, session_db, tt=None, tci=None):
    nid = nid.strip()
    npw = npw.strip()
    print(f"{nid} - 네이버 폐지 줍기 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    campaign_links = await fetch_url.fetch_naver_campaign_urls(session_db, nid)
    if campaign_links:
        async with async_playwright() as playwright:
            storage_state_path = Path(".auth").joinpath(f"auth-{nid}.json")
            storage_state = storage_state_path if storage_state_path.exists() else None
            device = playwright.devices['Galaxy S9+']
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=storage_state, **device)
            page = await context.new_page()
            login = await naver_login(page, nid, npw, tt, tci)
            if login:
                await process_campaign_links(page, campaign_links, session_db, nid)
                await send_telegram_message_if_needed(tt, tci, nid, campaign_links)
                if not os.path.exists('.auth'):
                    os.makedirs('.auth')
                    await context.storage_state(path=storage_state_path)
            await context.close()
    print(f"{nid} - 네이버 폐지 줍기 완료 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return campaign_links


async def process_with_telegram(naver_ids, naver_pws, telegram_tokens, telegram_chat_ids, session_db):
    for nid, npw, tt, tci in zip(naver_ids, naver_pws, telegram_tokens, telegram_chat_ids):
        tt = tt.strip()
        tci = tci.strip()
        await process_account(nid, npw, session_db, tt, tci)


async def process_without_telegram(naver_ids, naver_pws, session_db):
    for nid, npw in zip(naver_ids, naver_pws):
        await process_account(nid, npw, session_db)


async def main():
    naver_ids = os.environ.get("NAVER_ID").split('|')
    naver_pws = os.environ.get("NAVER_PW").split('|')
    telegram_token_txt = os.environ.get("TELEGRAM_TOKEN")
    telegram_chat_id_txt = os.environ.get("TELEGRAM_CHAT_ID")
    session_db = get_session()
    try:
        print("캠페인 URL 수집 시작 - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        await fetch_url.save_naver_campaign_urls(session_db)
        print("캠페인 URL 수집 완료 - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        if telegram_token_txt and telegram_chat_id_txt:
            telegram_tokens = telegram_token_txt.split('|')
            telegram_chat_ids = telegram_chat_id_txt.split('|')
            await process_with_telegram(naver_ids, naver_pws, telegram_tokens, telegram_chat_ids, session_db)
        elif not telegram_token_txt or not telegram_chat_id_txt:
            await process_without_telegram(naver_ids, naver_pws, session_db)
        session_db.commit()
    finally:
        session_db.close()


if __name__ == '__main__':
    asyncio.run(main())
