import os
import json
import time
import asyncio
from dotenv import load_dotenv
from telegram import Bot
import fetch_url
from datetime import datetime
from database import UrlVisit, CampaignUrl, get_session
from playwright.async_api import async_playwright

load_dotenv()


async def get_naver_session(context, nid, npw, tt, tci):
    page = await context.new_page()
    try:
        await page.goto("https://nid.naver.com/nidlogin.login")
        await page.locator("#id").fill(nid)
        await page.locator("#pw").fill(npw)
        await page.locator('button[type="submit"].btn_login').click()
        await page.wait_for_selector('//button[contains(@class, "btn_logout")]')
        state = await context.storage_state(path="state.json")
        print(f"{nid} - 네이버 로그인 성공 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return state is not None
    except Exception as e:
        print(f"{nid} - 네이버 로그인 실패 - {e} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await page.screenshot(path=f"login_error_{nid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        if tt and tci:
            await send_telegram_message(tt, tci, f"{nid} - 네이버 로그인 실패")
        return None


async def send_telegram_message(token, chat_id, message):
    bot = Bot(token=token)
    await bot.sendMessage(chat_id=chat_id, text=message)


async def check_cookie_and_login(context, nid, npw, tt, tci):
    storage_state_path = "state.json"
    if os.path.exists(storage_state_path):
        with open(storage_state_path, 'r') as f:
            storage_state = json.load(f)
            for cookie in storage_state.get('cookies', []):
                if cookie['name'] == 'PM_CK_loc':
                    if cookie['expires'] < time.time():
                        os.remove(storage_state_path)
                        print(f"{nid} - 이전 네이버 로그인 정보 제거 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        return await get_naver_session(context, nid, npw, tt, tci)
                    else:
                        print(f"{nid} - 이전 네이버 로그인 정보 사용 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        return True
    else:
        return await get_naver_session(context, nid, npw, tt, tci)


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
            iphone_13 = playwright.devices['iPhone 13']
            browser = await playwright.webkit.launch(headless=True)
            context = await browser.new_context(**iphone_13)
            state = await check_cookie_and_login(context, nid, npw, tt, tci)
            if state:
                context = await browser.new_context(**iphone_13, storage_state="state.json")
                page = await context.new_page()
                await process_campaign_links(page, campaign_links, session_db, nid)
                await send_telegram_message_if_needed(tt, tci, nid, campaign_links)
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
