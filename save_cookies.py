import asyncio
from playwright.async_api import async_playwright


async def naver_login(nid):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(**playwright.devices["iPhone 13"])
        page = await context.new_page()
        await page.goto("https://new-m.pay.naver.com/pcpay")
        await page.locator("#id").fill(nid)
        await asyncio.sleep(60)
        storage = await context.storage_state(path=nid + ".json")


if __name__ == '__main__':
    nid = input("네이버 로그인 전용 ID: ")
    asyncio.run(naver_login(nid))
