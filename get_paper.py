import os
import time
import asyncio
from dotenv import load_dotenv
from telegram import Bot
import fetch_url
import rsa
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import uuid
import lzstring
import re
from datetime import datetime
from database import UrlVisit, CampaignUrl, get_session

load_dotenv()


class NaverAccount:
    def __init__(self, nid, npw):
        self.nid = nid
        self.npw = npw

    def encrypt(self, key_str):
        def naver_style_join(l):
            return ''.join([chr(len(s)) + s for s in l])

        sessionkey, keyname, e_str, n_str = key_str.split(',')
        e, n = int(e_str, 16), int(n_str, 16)

        message = naver_style_join([sessionkey, self.nid, self.npw]).encode()

        pubkey = rsa.PublicKey(e, n)
        encrypted = rsa.encrypt(message, pubkey)

        return keyname, encrypted.hex()

    def encrypt_account(self):
        key_str = requests.get('https://nid.naver.com/login/ext/keys.nhn').content.decode("utf-8")
        return self.encrypt(key_str)

    def naver_session(self):
        encnm, encpw = self.encrypt_account()

        s = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
        s.mount('https://', HTTPAdapter(max_retries=retries))
        request_headers = {
            'User-agent': 'Mozilla/5.0'
        }

        bvsd_uuid = uuid.uuid4()
        encData = '{"a":"%s-4","b":"1.3.4","d":[{"i":"id","b":{"a":["0,%s"]},"d":"%s","e":false,"f":false},{"i":"%s","e":true,"f":false}],"h":"1f","i":{"a":"Mozilla/5.0"}}' % (
            bvsd_uuid, self.nid, self.nid, self.npw)
        bvsd = '{"uuid":"%s","encData":"%s"}' % (bvsd_uuid, lzstring.LZString.compressToEncodedURIComponent(encData))

        resp = s.post('https://nid.naver.com/nidlogin.login', data={
            'svctype': '0',
            'enctp': '1',
            'encnm': encnm,
            'enc_url': 'http0X0.0000000000001P-10220.0000000.000000www.naver.com',
            'url': 'www.naver.com',
            'smart_level': '1',
            'encpw': encpw,
            'bvsd': bvsd
        }, headers=request_headers)

        finalize_url = re.search(r'location\.replace\("([^"]+)"\)', resp.content.decode("utf-8")).group(1)
        s.get(finalize_url)

        return s


class TelegramMessenger:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    async def send_message(self, message):
        bot = Bot(token=self.token)
        await bot.sendMessage(chat_id=self.chat_id, text=message)


async def get_naver_session(nid, npw):
    account = NaverAccount(nid=nid, npw=npw)
    return account.naver_session()


async def process_campaign_links(session, campaign_links, session_db, nid):
    pattern = r"alert\('(.*)'\)"
    for link in campaign_links:
        response = session.get(link)
        lines = response.text.splitlines()

        for line in lines:
            match = re.search(pattern, line)
            if match:
                result_text = match.group(1)
                print(f"캠페인 URL: {link} - {result_text} - {datetime.now().strftime('%H:%M:%S')}")

                if '적립 기간이 아닙니다' in result_text:
                    campaign_url = session_db.query(CampaignUrl).filter_by(url=link).first()
                    if campaign_url:
                        campaign_url.is_available = False

        # Create a new UrlVisit object and add it to the session
        existing_visit = session_db.query(UrlVisit).filter_by(url=link, user_id=nid).first()
        if not existing_visit:
            session_db.add(UrlVisit(url=link, user_id=nid, visited_at=datetime.now()))

        response.raise_for_status()
        time.sleep(5)


async def send_telegram_message(campaign_links, nid):
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if telegram_token and telegram_chat_id:
        messenger = TelegramMessenger(token=os.environ.get("TELEGRAM_TOKEN"),
                                      chat_id=os.environ.get("TELEGRAM_CHAT_ID"))
        if not campaign_links:
            await messenger.send_message(f"{nid} - 더 이상 주울 네이버 폐지가 없습니다.")
        else:
            await messenger.send_message(
                f"{nid} - 모든 네이버 폐지 줍기를 완료했습니다. 적립 내역 확인 - https://new-m.pay.naver.com/pointshistory/list?category=all")
    else:
        pass


async def main():
    naver_ids = os.environ.get("NAVER_ID").split(',')
    naver_pws = os.environ.get("NAVER_PW").split(',')
    session_db = get_session()

    try:
        print("캠페인 URL 수집 시작 - " + datetime.now().strftime('%H:%M:%S'))
        await fetch_url.save_naver_campaign_urls(session_db)
        print("캠페인 URL 수집 완료 - " + datetime.now().strftime('%H:%M:%S'))
        for nid, npw in zip(naver_ids, naver_pws):
            nid = nid.strip()
            npw = npw.strip()
            print(f"네이버 ID: {nid} - 네이버 폐지 줍기 시작 - {datetime.now().strftime('%H:%M:%S')}")
            session = await get_naver_session(nid, npw)
            campaign_links = await fetch_url.fetch_naver_campaign_urls(session_db, nid)
            await process_campaign_links(session, campaign_links, session_db, nid)
            await send_telegram_message(campaign_links, nid)
            print(f"네이버 ID: {nid} - 네이버 폐지 줍기 완료 - {datetime.now().strftime('%H:%M:%S')}")

        session_db.commit()
    finally:
        session_db.close()


if __name__ == '__main__':
    asyncio.run(main())
