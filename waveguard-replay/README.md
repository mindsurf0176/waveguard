# WaveGuard CSI 리플레이

설치·서버·계정 없이 CSI 파일을 재생하는 한국어 오프라인 프로토타입입니다. **사람 감지 모델이 아닙니다.** 변화 점수는 단순 수치 휴리스틱이며 ML 분류 결과나 사람 존재 확률이 아닙니다.

## 1분 시작
1. ZIP을 압축 해제합니다.
2. `index.html`을 Chrome/Edge/Firefox/Safari 등 최신 **데스크톱 브라우저**에서 엽니다. 인터넷 연결이나 Node 설치는 실행에 필요하지 않습니다.
3. 기본 화면은 **합성 테스트 데이터**입니다. 재생 → 일시 정지 → 속도 변경 → 슬라이더 탐색을 사용해 보세요.
4. 실제 보드에서 기록한 헤더 포함 ESP-CSI CSV가 있다면 **CSV 가져오기**를 누릅니다. 외부 파일은 측정 진위를 검증하지 않습니다.

휴대전화의 파일 미리보기(특히 iOS)는 HTML 스크립트를 실행하지 않을 수 있으므로 데스크톱 브라우저를 권장합니다. 현재 환경에서는 데스크톱 브라우저별 호환성을 모두 검증하지 않았습니다.

## 들어 있는 파일
- `index.html`: 단독 실행 파일. 다른 파일 없이 복사해도 동작하도록 JS/CSS 내장.
- `synthetic-test-only.csv`: 이 프로젝트에서 만든 결정적 300프레임 합성 신호. 실제 RF 측정이 아니며 라이선스 불명 샘플을 가져오지 않았습니다.
- `core.js`, `app.js`, `template.html`: 수정용 소스.
- `build.js`: `node build.js`로 HTML/합성 CSV 재생성.
- `test.js`: `node --test test.js`로 파서/계산 단위 테스트.
- `app_test.js`: `node app_test.js`로 mock DOM 상태 전이 테스트(실제 브라우저 테스트 아님).
- `browser_test.py`: Playwright가 설치된 개발 환경의 별도 브라우저 검증용. 일반 사용에는 필요하지 않습니다.
- `VALIDATION.md`: 실제 실행한 검사와 검증 한계.

## CSV 계약
Espressif get-started의 헤더 기반 CSV를 대상으로 합니다. `type`, `len`, `data`, `first_word` 또는 `first_word_invalid`가 필요합니다. `local_timestamp`는 선택입니다. `id`와 C5/C6의 `seq` 모두 지원합니다. 일반 ESP32 및 C5/C6 헤더의 추가 열을 유지해 읽습니다. 헤더 없는 로그는 가져올 수 없습니다.

예시(설명용 합성, 실제 측정 아님):
```csv
type,id,mac,channel,local_timestamp,len,first_word,data
CSI_DATA,0,synthetic,6,1000000,6,0,"[3,4,0,5,6,8]"
CSI_DATA,1,synthetic,6,1100000,6,0,"[6,8,0,10,12,16]"
```
- `data`는 `[허수, 실수, 허수, 실수, ...]`의 signed int8 배열입니다.
- `len`은 배열의 바이트 수(원소 수)와 같아야 하며 2~4096 짝수만 허용합니다.
- 무효 첫 워드 플래그가 1이면 **첫 4바이트 = 첫 2쌍**을 계산에서 제외하고 배열 인덱스는 유지합니다.
- 최대 10 MB, 최대 20,000 유효 프레임. 줄바꿈을 포함하는 CSV 필드는 지원하지 않습니다.
- 잘못된 데이터 행은 제외하고 개수/최대 20개 상세 오류를 표시합니다. 유효 프레임이 하나도 없으면 이전 데이터를 유지하고 정지합니다. 주석/일반 로그 행은 무시합니다.
- `local_timestamp`는 µs 단위로 해석합니다. 모두 유효하고 엄격하게 증가할 때만 기록 간격을 사용합니다. 누락/중복/역행/랩어라운드는 임의 **10프레임/초** 모드로 전환하며 실제 측정 시간으로 표시하지 않습니다. 긴 간격은 그대로 유지되며 탐색 슬라이더로 건너뛸 수 있습니다.

## 계산과 한계
진폭은 `hypot(허수, 실수)`입니다. 변화 점수는 `100 × mean(abs(A현재 − A이전)) / max(mean(A이전), 1)`이며 두 프레임에서 모두 유효한 쌍만 사용합니다. 첫 프레임과 기록된 MAC/채널/배열 길이/일부 RF 설정이 달라지는 프레임은 비교하지 않습니다. 점수는 100을 넘을 수 있습니다. 무선 환경·AGC·패킷 설정·잡음도 점수에 영향을 줍니다.

그래프 가로축은 **원시 I/Q 쌍 인덱스**이지 물리적 부반송파 번호가 아닙니다. LTF 경계·DC/null·특수 STBC·패딩 처리를 완전히 하지 않습니다. 진폭은 보정된 물리 단위가 아닙니다. 신호가 끊기거나 잘못된 행이 제외되면 남은 인접 프레임을 비교하므로 시간 차이를 고려한 속도/활동량 척도도 아닙니다.

이 버전은 존재·위치·인원수·호흡·행동 판정 기능이 없습니다. 정확도 실험, 실제 보드 연동, 실제 측정 파일 검증을 하지 않았습니다. 일반 Mac Wi-Fi에서 CSI를 수집하지 않습니다. Web Serial, 시리얼 어댑터, 실시간 스트리밍도 구현하지 않았습니다. 추후 별도 시리얼 수집 어댑터가 헤더 포함 CSV를 제공하면 동일 파서 계약을 재사용할 수 있습니다.

## 개인정보/네트워크
CSV는 `File.text()`로 현재 브라우저 메모리에서만 처리합니다. 외부 요청, 분석 SDK, CDN, 업로드, localStorage가 없습니다. HTML의 CSP에서 네트워크 연결을 차단합니다. 페이지를 닫으면 데이터가 사라집니다. 파일에 포함된 장치 주소 등은 파일 자체에 남아 있으므로 공유할 때 주의하세요.

## 공식 형식 참고 (2026-10-27 확인)
- ESP-CSI get-started / CSI Data Format: https://github.com/espressif/esp-csi/blob/master/examples/get-started/README.md
- ESP-IDF Wi-Fi Channel State Information / first_word_invalid: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi-driver/wifi-vendor-features.html#wi-fi-channel-state-information

외부 저장소 코드를 실행하거나 가져와 포함하지 않았습니다. 형식 문서만 참고했습니다.
