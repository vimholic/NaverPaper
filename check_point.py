from lxml import html
import requests


async def check_point(session):
    url = "https://new-m.pay.naver.com/pointshistory/list?depth2Slug=event"
    response = session.get(url)
    response_text = response.text
    print(response_text)
    tree = html.fromstring(response_text)
    lists = tree.xpath('//*[@id="root"]//div[@class="infinite-scroll-component "]')
    for list in lists:
        print(list.text_content())


if __name__ == '__main__':
    session = requests.Session()
    check_point(session)
