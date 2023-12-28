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


async def main():
    account = NaverAccount(nid=os.environ.get("NAVER_ID"), npw=os.environ.get("NAVER_PW"))
    session = account.naver_session()

    campaign_links = await fetch_url.find_naver_campaign_links()

    messenger = TelegramMessenger(token=os.environ.get("TELEGRAM_TOKEN"), chat_id=os.environ.get("TELEGRAM_CHAT_ID"))

    if not campaign_links:
        await messenger.send_message("더 이상 주울 네이버 폐지가 없습니다.")
    else:
        pattern = r"alert\('(.*)'\)"
        for link in campaign_links:
            response = session.get(link)
            lines = response.text.splitlines()

            for line in lines:
                if re.search(pattern, line):
                    print(
                        f"캠페인 URL: {link} - {re.search(pattern, line).group(1)} - {datetime.now().strftime('%H:%M:%S')}")

            response.raise_for_status()
            time.sleep(5)
        await messenger.send_message("모든 네이버 폐지 줍기를 완료했습니다.")


if __name__ == '__main__':
    asyncio.run(main())
