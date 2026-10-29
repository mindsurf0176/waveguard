"""Optional local browser QA. Requires Python Playwright and Chromium.
Usage: CHROMIUM_PATH=/usr/bin/chromium python browser_test.py
No user files or network access. Screenshot is written outside this project.
"""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parent
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'), headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 1100})
    errors, external = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    def route(r):
        if not r.request.url.startswith('file:'):
            external.append(r.request.url)
            r.abort()
        else:
            r.continue_()
    page.route('**/*', route)
    page.goto((ROOT/'index.html').as_uri())
    assert page.locator('#frame').inner_text() == '1 / 300'
    assert '합성 테스트' in page.locator('#badge').inner_text()
    for _ in range(3):
        page.locator('#play').click()
        page.wait_for_timeout(250)
        page.locator('#play').click()
        assert page.locator('#status').inner_text() == '일시 정지'
        page.locator('#reset').click()
        assert page.locator('#frame').inner_text() == '1 / 300'
    page.locator('#speed').select_option('4')
    page.locator('#play').click()
    page.wait_for_timeout(500)
    assert int(page.locator('#frame').inner_text().split(' / ')[0]) > 5
    page.locator('#seek').fill('150')
    assert page.locator('#frame').inner_text() == '151 / 300'
    assert page.locator('#status').inner_text() == '일시 정지'
    page.locator('#reset').click()
    for _ in range(2):
        page.locator('#file').set_input_files(str(ROOT/'synthetic-test-only.csv'))
        expect(page.locator('#source')).to_have_text('synthetic-test-only.csv')
        assert '합성 테스트' in page.locator('#badge').inner_text()
    valid = 'type,id,len,first_word,data\nCSI_DATA,0,4,0,"[3,4,6,8]"\nCSI_DATA,1,4,0,"[6,8,3,4]"\n'
    page.locator('#file').set_input_files({'name':'valid.csv','mimeType':'text/csv','buffer':valid.encode()})
    expect(page.locator('#frame')).to_have_text('1 / 2')
    assert '미검증' in page.locator('#badge').inner_text()
    assert '10프레임' in page.locator('#timeMode').inner_text()
    page.locator('#file').set_input_files({'name':'bad.csv','mimeType':'text/csv','buffer':b'not csi'})
    expect(page.locator('#notice')).to_contain_text('파일을 열 수 없습니다')
    assert page.locator('#source').inner_text() == 'valid.csv'
    expect(page.locator('#frame')).to_have_text('1 / 2')
    page.locator('#demo').click()
    page.locator('#seek').fill('299')
    page.locator('#play').click()
    assert int(page.locator('#frame').inner_text().split(' / ')[0]) < 10
    page.locator('#reset').click()
    page.locator('#seek').fill('130')
    page.screenshot(path=str(ROOT.parent/'waveguard-qa.png'), full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(ROOT.parent/'waveguard-qa-mobile.png'), full_page=True)
    assert not errors, errors
    assert not external, external
    browser.close()
    print('PASS: offline load, repeated playback/reset/import, speed, seek, malformed import retention, synthetic restore, end restart, responsive width, no external requests')
