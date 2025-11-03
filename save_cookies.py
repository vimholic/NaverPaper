import asyncio
from playwright.async_api import async_playwright
from config import Config


async def naver_login(nid):
    """
    네이버 로그인 쿠키를 로컬에서 생성합니다.

    캡차 등으로 서버에서 로그인이 안 되는 경우, 로컬 PC에서 이 스크립트를 실행하여
    쿠키 파일({사용자ID}.json)을 생성하고 서버로 업로드하여 사용할 수 있습니다.

    Args:
        nid (str): 네이버 로그인 ID
    """
    print(f"\n네이버 로그인 쿠키 생성 시작...")
    print(f"대기 시간: {Config.LOGIN_WAIT_TIMEOUT}초")
    print(f"(이 시간 동안 수동으로 로그인을 완료해주세요)\n")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(**playwright.devices["iPhone 13"])
        page = await context.new_page()
        await page.goto("https://new-m.pay.naver.com/pcpay")
        await page.locator("#id").fill(nid)

        print(f"\n{Config.LOGIN_WAIT_TIMEOUT}초 동안 대기합니다...")
        print("브라우저에서 수동으로 로그인을 완료해주세요.")
        await asyncio.sleep(Config.LOGIN_WAIT_TIMEOUT)

        storage = await context.storage_state(path=nid + ".json")
        print(f"\n✓ 쿠키 파일 생성 완료: {nid}.json")
        print(f"이 파일을 서버로 업로드하여 사용하세요.")


if __name__ == '__main__':
    nid = input("네이버 로그인 전용 ID: ")
    asyncio.run(naver_login(nid))
