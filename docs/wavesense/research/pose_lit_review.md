# WaveSense 자세(포즈) 추정 문헌 조사 — 전체본
작성: 2026-11-18 (KST). 모든 항목은 논문 PDF/초록 페이지 또는 데이터셋 페이지를 직접 열어 확인했다. 확인하지 못한 항목은 **[미확인]**으로 표시했다. 수치는 논문 본문에서 그대로 옮겼다(단위·지표 정의가 논문마다 달라서 서로 직접 비교하면 안 됨).

## 1. 기초 연구: 전신 포즈 / 스켈레톤

### 1-1. Person-in-WiFi: Fine-grained Person Perception using WiFi — ICCV 2019
- 저자: Fei Wang, Sanping Zhou, Stanislav Panev, Jinsong Han, Dong Huang. 링크: https://arxiv.org/abs/1904.00276 (ICCV 2019는 DensePose 논문 참고문헌 [31]에서 확인. CVF 페이지는 직접 열지 않음)
- 하드웨어: Tx 1세트, Rx 1세트, 각각 안테나 3개를 일렬 배치(3×3 = 9쌍). 2.4GHz, 20MHz, 서브캐리어 30개. 상용 NIC + 오픈소스 CSI 툴(Halperin et al. 2011, 본문에 NIC 모델명은 링크로만 표기). CSI 100Hz, 영상 20FPS.
- 라벨: 수신기에 붙인 RGB 카메라 영상에 Mask R-CNN(분할), OpenPose Body-25(관절 히트맵·PAF)를 돌려 자동 생성.
- 데이터: 16개 장면(실험실 6, 강의실 10), 8명, 동시 1~5명, 학습 123,631 / 테스트 30,996 프레임.
- 결과(같은 환경): 분할 mIoU 0.65, mAP 0.38(AP@50 0.91). 수작업 라벨 160개 기준 포즈 mPCK@0.20 78.75(OpenPose 89.48).
- **교차 환경**: 14개 장면 학습, 2개 장면 테스트에서 분할 mIoU 0.12, 포즈 mPCK@0.20 19.34. GAN 기반 적응으로 0.24, 31.06까지 올렸지만 "더 많은 데이터와 라벨이 필요하다"고 직접 씀.

### 1-2. Can WiFi Estimate Person Pose? (WiSPPN) — arXiv 2019
- 저자: Fei Wang, Stanislav Panev, Ziyi Dai, Jinsong Han, Dong Huang. 링크: https://arxiv.org/abs/1904.00277 (학회 게재 여부는 확인 못 함 → arXiv 프리프린트로 표기)
- 하드웨어: 3안테나 송신기 + 3안테나 수신기, 2.4GHz. 수신기에 720p 카메라 정렬. CSI 100Hz, 영상 20Hz.
- 라벨: AlphaPose(18 관절)를 교사 네트워크로 사용.
- 모델: 완전 합성곱 네트워크(FCN).
- 데이터: 80k+ 프레임, 16개 장소(방 2개), 8명. 단일 인물.
- 결과: 18관절 평균 PCK@20 0.38, PCK@50 0.82. 교차 환경 실험은 없음.

### 1-3. Towards 3D Human Pose Construction Using WiFi (WiPose) — ACM MobiCom 2020
- 저자: Wenjun Jiang, Hongfei Xue, Chenglin Miao, Shiyang Wang, Sen Lin, Chong Tian, Srinivasan Murali, Haochen Hu, Zhi Sun, Lu Su. 링크: https://doi.org/10.1145/3372224.3380900 , PDF https://wenjunjiang.github.io/MobiCom2020.pdf
- 하드웨어: Intel 5300 NIC 4대(노트북 1대 = Tx, 안테나 1개 사용 / 데스크톱 3대 = Rx, 각 안테나 3개를 분산 배치 → 수신 안테나 9개). 5.825GHz(ch165), 20MHz, 1000 패킷/s.
- 라벨: VICON 모션캡처(3D).
- 모델: CNN + LSTM, 스켈레톤 사전지식(순운동학), 입력은 CSI 또는 3D 속도 프로파일(3DVP).
- 결과: 기본 환경 평균 관절 오차 2.83cm(레이더용 기존 모델보다 35% 개선).
- **교차 환경**: VICON이 있는 방이 하나뿐이라 같은 방의 설정을 바꿔 테스트했다. 가구 추가 / 가림막 / 안테나 무작위 배치에서 3DVP 입력 기준 61.2 / 79.1 / 87.7mm, CSI 입력 기준 95.3 / 121.6 / 95.2mm.
- 주의: 3DVP는 정적 물체 정보를 지우도록 설계된 것이라, 논문 스스로 "모든 신체 부위가 항상 움직이지는 않아서 자세 정보 손실이 생긴다"고 씀(정지한 사람에게 불리).

### 1-4. DensePose From WiFi — arXiv 2022 (프리프린트)
- 저자: Jiaqi Geng, Dong Huang, Fernando De la Torre (CMU). 링크: https://arxiv.org/abs/2301.00250 (학회 게재 여부 확인 못 함)
- 하드웨어/데이터: 송신 안테나 3 × 수신 안테나 3, 2.4GHz±20MHz에서 서브캐리어 30개, CSI 100Hz, 영상 20FPS. **Person-in-WiFi 데이터셋([31])을 그대로 사용.** "TP-Link AC1750 같은 3안테나 라우터 2대면 된다"는 비용 언급이 있지만, 실험은 그 데이터셋으로 함.
- 라벨: 사람이 단 라벨 없음. 이미지 기반 DensePose-RCNN(R101)의 출력을 의사 정답(R101-Pseudo-GT)으로 사용.
- 모델: 진폭+위상 → 모달리티 변환 네트워크 → DensePose-RCNN 구조(UV 맵 24부위 + 17 키포인트), 이미지 모델로 전이학습.
- 결과(같은 레이아웃): 사람 검출 AP 43.5 / AP@50 87.2. dpAP·GPS 45.3 / GPS@50 79.3(이미지 모델은 81.8 / 93.7).
- **교차 레이아웃**(15개 학습 → 1개 테스트): AP 43.5 → 27.3, dpAP·GPS 45.3 → 25.4. 논문도 "학습하지 않은 레이아웃에 배포하는 건 매우 어려운 문제"라고 씀.

### 1-5. MetaFi: Device-Free Pose Estimation via Commodity WiFi for Metaverse Avatar Simulation — IEEE WF-IoT 2022
- 저자: Jianfei Yang, Yunjiao Zhou, He Huang, Han Zou, Lihua Xie. 링크: https://arxiv.org/abs/2208.10414 , DOI https://doi.org/10.1109/WF-IoT54382.2022.10152057 (DOI는 검색 결과로만 확인)
- 하드웨어: TP-Link N750 라우터 2대(OpenWrt + Atheros CSI 툴 계열), Tx 안테나 1 / Rx 안테나 3, 안테나 쌍마다 서브캐리어 114개, 진폭만 사용. CSI 약 1000Hz, 영상 약 31Hz. 카메라와 수신기는 높이 1m.
- 라벨: HRNet(MMPose) 17 관절(교차 모달 지도학습).
- 모델: WPNet(CNN + 잔차 블록).
- 결과: 13명 × 6분, 무작위 60/20/20 분할에서 평균 PCK@50 95.23%, PCK@20 83.16%. 손목은 PCK@50 73~74%로 가장 낮음. 교차 환경 실험은 없고, 무작위 프레임 분할이라 낙관적.

### 1-6. MM-Fi: Multi-Modal Non-Intrusive 4D Human Dataset for Versatile Wireless Sensing — NeurIPS 2023 Datasets & Benchmarks
- 저자: Jianfei Yang 외 8명. 링크: https://arxiv.org/abs/2305.10345
- 하드웨어: TP-Link N750 AP 2대 + Atheros CSI 툴, 5GHz, 40MHz, 서브캐리어 114개, Tx 안테나 1 / Rx 안테나 3. 그 밖에 LiDAR, mmWave, RGB-D 동시 수집.
- 데이터: 40명, 27개 동작, 320k+ 동기 프레임. 3D 포즈 라벨 포함.
- 결과(WiFi, 3D 포즈 MPJPE, 프로토콜 1): 무작위 분할 186.9mm → 교차 대상자 222.3mm → **교차 환경 367.8mm**(환경 3곳 학습, 1곳 테스트). 논문도 WiFi의 해상도 한계를 지적함.

### 1-7. Person-in-WiFi 3D: End-to-End Multi-Person 3D Pose Estimation with Wi-Fi — CVPR 2024 ★우리 셋업과 가장 비슷함
- 저자: Kangwei Yan, Fei Wang, Bo Qian, Han Ding, Jinsong Han, Xing Wei. 링크: https://openaccess.thecvf.com/content/CVPR2024/papers/Yan_Person-in-WiFi_3D_End-to-End_Multi-Person_3D_Pose_Estimation_with_Wi-Fi_CVPR_2024_paper.pdf , 프로젝트 https://aiotgroup.github.io/Person-in-WiFi-3D/
- 하드웨어: **Tx 1대 + Rx 3대를 사각형 영역 모서리에 배치**, 모두 Intel 5300(Rx마다 안테나 3개), 5.64GHz(ch128), 서브캐리어 30개, 300 패킷/s. 영역 4m×3.5m.
- 라벨: Azure Kinect Body Tracking SDK(3D, 14 관절).
- 모델: Transformer/DETR 방식 종단간 다인 포즈.
- 결과: 7명, 97K+ 프레임. MPJPE 91.7mm(1명) / 108.1mm(2명) / 125.3mm(3명).
- **Rx 개수 줄이기**: Rx 3대 107.2mm → Rx 2대 142.8~148.5mm → Rx 1대 173.0mm.
- **진폭만 쓰면**: 192.4mm. 위상 추가 시 137.7mm, 위상 잡음 제거까지 하면 107.2mm.
- **교차 대상자 131.6mm, 교차 환경 626.4mm.** 한계로 "Kinect SDK가 라벨 상한을 정한다", "장비 4대의 위치·높이·안테나 방향을 다른 장소에서 맞추기 어려워 교차 장소 일반화가 어렵다"고 씀.

### 1-8. 참고만(본문 확인 안 함 또는 일부만)
- From Point to Space: 3D Moving Human Pose Estimation Using Commodity WiFi (Wi-Mose), IEEE Communications Letters 2021, https://arxiv.org/abs/2012.14066 — 초록만 확인. P-MPJPE LoS 29.7mm / NLoS 37.8mm.
- GoPose, Winect: Person-in-WiFi 3D가 "Tx 1 + Rx 4 구성"이라고 언급하는 것만 확인 **[원문 미확인]**.
- CSI-Former / Wi-Pose 데이터셋(Entropy 2023, https://www.mdpi.com/1099-4300/25/1/20) — 검색 결과 초록만 확인 **[원문 미확인]**.

## 2. 저가형 / ESP32 연구와 공개 데이터

### 2-1. ESP32 CSI 수집 도구
- Hernandez & Bulut, "Lightweight and Standalone IoT Based WiFi Sensing for Active Repositioning and Mobility", IEEE WoWMoM 2020 (DOI 10.1109/WoWMoM49955.2020.00056, PDF https://ebulutvcu.github.io/wowmom20-WiFiSensing.pdf). ESP32로 CSI를 직접 받는 도구(ESP32 CSI Toolkit)를 공개했다. 실험은 활동 인식이고 포즈는 아님.

### 2-2. Strohmayer & Kampel (TU Wien) ESP32-S3 계열 ★Wallhack1.8k와 같은 그룹
- **On the Generalization of WiFi-Based Person-Centric Sensing in Through-Wall Scenarios**, ICPR 2024(LNCS 15315, Springer 2025), DOI https://doi.org/10.1007/978-3-031-78354-8_13 — **3DO 데이터셋** 논문. 3DO 정보는 Zenodo 페이지에서 확인했고 논문 본문은 직접 안 열었음.
  - **3DO 데이터셋**(https://zenodo.org/records/10925351, 435MB): 1명, 벽 너머 시나리오, 3일 연속. 5분 녹화 42개(약 125만 패킷). 패킷마다 **클래스 라벨(배경 0 / 걷기 1 / 앉기 2 / 눕기 3) + 3D 궤적 라벨**, 날마다 10분 배경 녹화 3개.
  - 논문이 정한 분할은 1일차 학습, 2·3일차 테스트. 2일차는 동적 변화, 3일차는 가구 재배치(정적 변화)다.
  - 라이선스 표기가 Zenodo 메타데이터는 CC-BY-4.0, 설명문은 "비상업 연구용"이라 서로 다름. 비상업으로 쓰면 문제 없음.
- **WiFlexFormer: Efficient WiFi-Based Person-Centric Sensing**, arXiv 2024 (https://arxiv.org/abs/2411.04224) — 3DO로 평가.
  - 장비: ESP32-S3-DevKitC-1U + ALFA APA-M25 지향성 안테나, 100Hz, 영상으로 라벨.
  - 앉기 클래스는 의자 2개를 오가며 머리·팔·다리를 무작위로 움직이고, 눕기는 낙상 상황을 흉내낸 것이다. 즉 "완전 정지"가 아니다.
  - 진폭 특징 정확도: 1일차(같은 날) 98.01~99.38% → 2일차 80.01~88.03% → 3일차(가구 재배치) 70.49~86.98%. WiFlexFormer는 98.41 / 85.26 / 86.98%.
- **Through-Wall Imaging based on WiFi Channel State Information (WiFiCam)**, arXiv 2024 (https://arxiv.org/abs/2401.17417): ESP32-S3 + 지향성 안테나 CSI → 이미지 합성(VAE). 스켈레톤은 아니지만 ESP32 CSI로 사람 모습을 복원한 사례.
- **Directional Antenna Systems for Long-Range Through-Wall HAR**, IEEE ICIP 2024 (https://arxiv.org/abs/2401.01388): Wallhack1.8k 원 논문. NLOS 활동 인식 92.0±3.5%(BQ), 86.8±4.7%(PIFA).

### 2-3. ESP32 낙상·자세 데이터와 논문
- **WiFall**(ESP32-S3, https://github.com/RS2002/KNN-MMD/blob/main/WiFall/README.md): 회의실, 2.4GHz 20MHz, 서브캐리어 52개, 약 100Hz, 기기당 안테나 1개. 사람 ID별 fall / jump / sit / stand / walk.
  - 관련 논문: Zhao et al., "KNN-MMD: Cross Domain Wireless Sensing via Local Distribution Alignment", arXiv 2024 (https://arxiv.org/abs/2412.04783). 교차 도메인 퓨샷 정렬 방법.
  - 이 데이터셋으로 본문 수치는 확인 안 함 **[수치 미확인]**.
- **A Proof-of-Concept Study of Wi-Fi CSI-Based Fall Detection Using ESP32 Devices**, arXiv 2026-11-11 (https://arxiv.org/abs/2611.15532, 프리프린트): ESP32 2대, 거리 3.5m. 테스트 29건(낙상 16, 걷기 13)에서 정확도 93.10%. 교차 환경·교차 대상자 검증은 없음.
- **Channel state information-based fall detection using IoT devices**, CNIoT 2023(SPIE), DOI 10.1117/12.3010434: 서지정보만 확인 **[본문·수치 미확인]**.
- **esp32s3-csi-har-2025**(Hugging Face, Marcolini): 앉기/서기/걷기/눕기 각 20개 녹화. 보드 1개, 사람 1명, 장소 1곳, 빈 방 없음. README 자체가 "교차 검증 없음, 단일 분할 0.7768"이라고 밝힘. 커뮤니티 데이터라 동료 검토를 거치지 않았음 **[검색 결과로만 확인]**.

### 2-4. 우리가 이미 가진 데이터의 라벨
- **Wallhack1.8k**: 빈 방 / 걷기 / 걷기+팔 흔들기 + 방 번호 1~5. **자세(서기·앉기·눕기) 라벨 없음.**
- **TU Wien ICVS 2023**: DP = 빈 방/방 1~5, DA = 활동 없음/걷기/걷기+팔. **자세 라벨 없음.**
- → 자세 사전검증에는 **3DO**(앉기·눕기·걷기·배경 + 3D 궤적, 3일)를 써야 한다. 스켈레톤 라벨이 있는 공개 ESP32 데이터는 찾지 못했다(못 찾았다는 것이지 없다는 뜻은 아님).

## 3. 우리 셋업(ESP32 Tx 1 + Rx 3, 2×2 구역 방, 웹캠은 라벨용) 기준 현실성

**하드웨어 차이**
- 논문들은 대부분 Intel 5300이나 Atheros를 썼다. Rx마다 안테나 3개, 서브캐리어 30~114개, 300~1000 패킷/s.
- ESP32는 보드당 안테나 1개다. 공개 데이터 기준 2.4GHz 20MHz에서 서브캐리어 52개(우리 Wallhack 분석에선 108슬롯), 약 100Hz.
- 보드끼리 클럭이 공유되지 않아 위상을 쓰기 어렵다(Person-in-WiFi 3D도 위상 잡음 제거가 핵심이었음). 실질적으로 진폭 위주가 될 텐데, Person-in-WiFi 3D에서 진폭만 쓰면 오차가 107mm에서 192mm로 커졌다.

**Stage 1 — 거친 자세 분류(없음/서기·걷기/앉기/눕기, 구역별): 현실적**
- 3DO에서 ESP32-S3로 같은 날 98~99%, 다른 날 70~88%가 나왔다. 우리 방에서, 같은 배치로, 날짜를 나눠 평가하면 수치를 낼 수 있다.
- 다만 3DO의 앉기·눕기도 몸을 움직인 상태라, 완전히 가만히 있는 사람은 따로 검증해야 한다.

**Stage 2 — 스켈레톤: "같은 방·같은 배치·같은 사람"이라는 조건을 단 데모 수준이 현실적**
- 근거 1: 가장 비슷한 구성(Tx 1 + Rx 3 모서리, Person-in-WiFi 3D)도 Rx마다 안테나 3개 + 위상 + 수십만 프레임이었다. 교차 환경은 626mm까지 무너졌다.
- 근거 2: MM-Fi도 교차 환경에서 368mm였다.
- 근거 3: ESP32로 스켈레톤을 회귀한 동료 검토 논문은 찾지 못했다.
- 권장 형태: 웹캠 + 포즈 모델(MediaPipe/OpenPose/YOLO-pose 등)로 교사 라벨을 만들고, 관절 수를 줄인다(예: 머리·몸통·골반·무릎 수준). 평가는 녹화·날짜 단위로 분리하고 PCK/MPJPE를 보고한다. 성공 기준은 "Stage 1 분류보다 나은 정보를 주는가"로 잡는다.

**알려진 실패 요인**
1. 도메인 변화: 날짜, 가구, 장비 위치, 사람이 바뀌면 크게 떨어진다(위 수치들, 우리 Wallhack 실험도 동일).
2. 정지한 사람: 움직임 기반 특징·속도 프로파일은 정적 자세 정보를 잃는다(WiPose도 언급). 공개 ESP32 데이터는 대부분 움직이는 사람이다.
3. 여러 명: 인원이 늘면 오차가 는다(Person-in-WiFi 3D 1→3명에서 91.7→125.3mm). 라벨링 도구(Kinect SDK)도 3명을 넘으면 불안정했다.
4. 라벨 품질: 카메라 포즈 모델 출력이 상한이고, 가려진 신체는 라벨이 틀린다(Person-in-WiFi에서 단일 카메라 가림 문제를 지적). 우리 목적(CCTV 사각지대)과 충돌한다. 웹캠은 학습용으로 사각지대도 볼 수 있는 위치에 둬야 한다.
5. Rx 수: Rx를 줄이면 성능이 떨어진다(3→1대: 107→173mm). Rx 3대는 최소 구성으로 보는 게 맞다.

## 4. 포스터 인용 추천
1. Person-in-WiFi 3D (CVPR 2024): Tx 1 + Rx 3 모서리 배치 근거, Rx 수·위상 영향, 교차 환경 한계
2. Person-in-WiFi (ICCV 2019): 카메라 포즈 모델로 WiFi 포즈를 교사 학습하는 방식의 원조
3. DensePose From WiFi (arXiv 2022): 대표성 있는 후속 연구, 교차 레이아웃 성능 하락 수치. 프리프린트임을 표기
4. 3DO / On the Generalization… (ICPR 2024): ESP32-S3 자세(앉기·눕기) 분류와 날짜 간 일반화
5. (선택) MM-Fi (NeurIPS 2023 D&B): 교차 환경 수치, 공개 벤치마크
6. (기존 유지) Wallhack1.8k(ICIP 2024), TU Wien ICVS 2023

## 5. 미확인 / 한계 목록
- Person-in-WiFi의 ICCV 게재는 DensePose 논문 참고문헌으로 확인. CVF 페이지는 직접 안 열었다.
- WiSPPN, DensePose From WiFi의 정식 학회 게재 여부는 확인 못 해서 arXiv로 표기했다.
- MetaFi의 WF-IoT DOI는 검색 결과로만 확인했다.
- GoPose, Winect, CSI-Former, SPIE 낙상 논문, HF esp32s3-csi-har-2025는 원문이나 수치를 직접 검증하지 않았다.
- 3DO 논문(ICPR 2024) 본문은 안 열었고, 수치는 WiFlexFormer 논문에서 가져왔다.
- 검색은 공개 웹 기준이다. 유료 DB(IEEE Xplore/ACM 전문)는 직접 검색하지 않았다.

---

# 2부. Wi-Fi CSI 인원 추정(crowd/occupancy counting): 최대 몇 명까지 셀 수 있나 (2026-11-18 추가)

질문: "보안용으로 쓰려는데 인원 추정은 최대 몇 명까지 되나?"
원칙: 각 출처를 이번에 직접 열어 봤다. 본문을 못 연 것은 **[초록만]**, 남의 논문에 인용된 숫자는 **[2차 인용]**이라고 표시했다. 숫자는 지어내지 않았다.

## 2-1. 요약 표

| 논문 / 데이터 | 하드웨어 | 최대 인원 | 그 인원에서의 성능 | 사람 상태 | 교차 환경 |
|---|---|---|---|---|---|
| Wi-CaL (IEEE Access 2022) | **ESP32 4쌍(링크 4개), 방을 4구역으로 나눔** | 5명(5.5×5.5m) / 10명(11×5.5m) | 세션 하나를 빼고 검증했을 때 중앙값 절대오차 0.35 / 0.41명, 오차가 1명 이내인 비율 89.8% / 81.8% | 걷는 중 | 다른 날로만 검증. 다른 방은 미실험 |
| WiCount 데이터셋 (CSI-BERT2, IEEE TMC 2025) | **ESP32-S3 Rx 1대, 안테나 1개**, 공유기 Tx | 3명 (0~3명, 4클래스) | 정확도 94.32%(CSI-BERT2). MLP 56.77%, CNN 69.68% | 걷기, 쪼그려 앉기, 점프, 앉기 섞임 | 회의실 1곳만 |
| Jamal & Bettstetter (EW 2025) | 802.11ac NIC 2×2, PicoScenes, 22m² 사무실 | 6명 | KNN 전체 98.0%, 6명일 때 97.1%. SVM 전체 89.3%. 사람 있음/없음은 100% | 서 있거나 이따금 걷기 | 방 1곳만 |
| Electronic Frog Eye / FCC (INFOCOM 2014) | Intel 5300 노트북. 홀 확장 실험은 Rx 4대를 모서리에, Tx 1대를 가운데 | 30명 | 15명이 넘으면 평균 오차 약 2명, 27명이 넘으면 5명 넘게 틀림. 지표(PEM)는 20~22명 근처에서 포화 | **움직이는 사람만** | 실내 기준 오차 2명 미만이 98% 이상, 실외는 오차가 약 2명인 경우가 약 70% |
| Brena 외 (Electronics 2021, Di Domenico 데이터셋) | AP(안테나 2) → Intel 5300(안테나 3), 링크 6개 | 8명 | 링크 1개면 44%, 6개 다 쓰면 99% 이상 | 자유롭게 움직임 | 방 3곳 각각 따로 학습했고 방 사이 이전은 아님 |
| Torun·Parsay·Mostofi (IEEE JSAS 2025) | Intel 5300 노트북 2대 | 13명 | 실험 42번 전체 평균 절대오차 1.04명 | **앉아 있는 사람**(몸을 꼼지락대는 움직임 이용) | 현장 CSI로 학습하지 않음(온라인 영상으로 모델을 만듦). 사무실·회의실 2곳 |
| WiCount (Liu 외, ISPA 2017) **[초록만]** | 상용 Wi-Fi | 5명 | 82.3% | 미확인 | 미확인 |
| FreeCount (Zou 외, GLOBECOM 2017) **[초록만]** | 상용 공유기(OpenWrt) | 7명 **[2차 인용]** | 96%. 7명 클래스는 81.8% **[2차 인용]** | 동작 기반 | 초록에 "시간·환경 변화에도 일관"이라고만 씀 |
| Zhou 외 (Wireless Networks 2020) **[초록만]** | Tx·Rx 1쌍 | 34명 | 오차 1명 이내 97.7%, 2명 이내 99.3%. 6명 규모에서는 1명 이내 100% | 미확인 | 미확인 |
| Person-in-WiFi 3D (CVPR 2024), 포즈 논문 | Tx 1 + Rx 3(Intel 5300) | 3명 | 관절 위치 평균 오차(MPJPE)가 1명 91.7mm → 2명 108.1mm → 3명 125.3mm | 동작 수행 | 다른 환경에서 626.4mm |
| MM-Fi (NeurIPS 2023 D&B), 포즈 데이터셋 | TP-Link AP 2대(Atheros) | **1명** | 해당 없음. 한계 절에 "한 사람, 3m 거리, 같은 방향"이라고 명시 | 동작 수행 | 이 섹션에서는 해당 없음 |

## 2-2. 논문별 상세

### Wi-CaL: WiFi Sensing and Machine Learning Based Device-Free Crowd Counting and Localization, IEEE Access vol.10, 2022 ★우리와 가장 가까움
- 저자: H. Choi 외. 링크: https://doi.org/10.1109/ACCESS.2022.3155812 (오픈 액세스, CC BY). 코드·데이터: https://github.com/narajinx/Wi-CaL-WiFi-Crowd-Estimation
- 하드웨어: ESP32 노드 4쌍(안테나 1개)과 ESP32 CSI Toolkit, 100 패킷/s, 서브캐리어 52개 중 13개 사용. 링크 4개를 가로·세로·대각선으로 영역을 가로지르게 배치했다.
- 공간: 회의실 5.5×5.5m(최대 5명), 세미나실 11×5.5m(최대 10명). 두 방 모두 **4구역으로 나눠** 사람이 어느 구역에 모였는지도 맞혔다. 우리 2×2 구역과 같은 구조다.
- 결과: 같은 날 데이터 안에서 k-fold로 검증하면 중앙값 절대오차가 회의실 0.13~0.18, 세미나실 0.32~0.36이었다. 날을 바꿔 검증하면(세션 하나를 뺌) 0.35(1명 이내 89.8%), 0.41(1명 이내 81.8%)로 나빠졌다. 구역 맞히기는 91.4%와 98.1%였다. Frog Eye의 PEM 지표를 같은 데이터에 쓰면 중앙값 절대오차 0.62, 1명 이내 66.5%였다.
- 한계(논문이 직접 씀): 다른 날 데이터로 테스트하면 정확도가 떨어진다. 다른 방에 옮겨 검증하는 실험은 향후 과제로 남겼다. CSI 변동이 어느 인원에서 포화될 것으로 본다. 인원 수별 오차가 어떻게 변하는지는 본문 숫자로 따로 주지 않았다. 사람은 모두 걷는 상태였고 한 구역에 모여 있거나 전체에 퍼져 있었다. 여러 무리가 나뉘어 있는 경우는 다루지 않았다.

### WiCount 데이터셋: CSI-BERT2, IEEE TMC 2025 (arXiv 2412.06861)
- 링크: https://arxiv.org/abs/2412.06861 , 데이터 https://huggingface.co/datasets/RS2002/WiCount
- 2017년 WiCount 논문과 이름만 같고 다른 것이다. ESP32-S3 Rx 1대, 안테나 1개, 서브캐리어 52개, 100Hz, Tx는 가정용 공유기. 작은 회의실에서 0~3명을 모았다.
- 사람들은 걷기, 쪼그려 앉기, 점프, 앉기 등을 자연스럽게 섞어서 했다.
- 원본 데이터 기준 인원 분류 정확도: CSI-BERT2 94.32%, CSI-BERT 89.67%, RNN 80.93%, LSTM 80.72%, CNN 69.68%, MLP 56.77%.
- 인원 수별 정확도와 교차 환경 실험은 없다. 방이 하나뿐이다.

### Experiments on Detecting and Counting People via Ambient Wi-Fi, European Wireless 2025 (Jamal & Bettstetter)
- 링크(저자 원고): https://data.bettstetter.com/publications/jamal-2025-ew-wifisensing-preprint.pdf
- 하드웨어: 802.11ac 5GHz, 2×2 MIMO, PicoScenes. 사무실 22m².
- 0~6명을 7개 클래스로 분류했다. 사람들은 서 있거나 이따금 다른 위치로 걸어갔다.
- 클래스별 정확도(%, 0/1/2/3/4/5/6명, ">1명", 전체):
  - KNN: 100 / 99.2 / 99.0 / 97.5 / 97.0 / 96.4 / 97.1, ">1명" 99.0, 전체 98.0
  - NN: 100 / 96 / 91.0 / 88 / 92.0 / 91.3 / 91.4, ">1명" 97.0, 전체 92.6
  - SVM: 100 / 95.2 / 87.0 / 83.0 / 87.0 / 85.3 / 89.0, ">1명" 97.0, 전체 89.3
- 초록에는 "전체 최대 90%, 가장 나쁜 클래스 80%"라고 써서 본문 표(KNN 98%)와 맞지 않는다. 방이 하나뿐이고 교차 환경 실험은 없다. "0 / 1 / 2명 이상" 세 구간은 각각 99% 이상으로 구분했다고 보고했다.

### Electronic Frog Eye: Counting Crowd Using WiFi (FCC), IEEE INFOCOM 2014
- 저자: Wei Xi 외. 링크: https://doi.org/10.1109/INFOCOM.2014.6847958 . 본문은 http://www.cs.iit.edu/~xli/paper/Conf/Frogeye-info14.pdf (원 서버가 응답하지 않아 Wayback 스냅샷으로 열었다)
- 하드웨어: Intel 5300 노트북. 지표는 PEM(팽창시킨 CSI 행렬에서 0이 아닌 원소의 비율)이고, Grey Verhulst 모델로 인원을 추정한다. 0~N명 데이터로 보정해야 한다.
- 최대 30명. 홀에 노트북 4대(Rx)를 모서리에, 1대(Tx)를 가운데 두었다.
  - 15명이 넘으면 평균 오차가 약 2명, 27명이 넘으면 5명이 넘는다.
  - PEM은 20명이 넘으면 증가가 둔해지고 22명이 넘으면 거의 멈춘다.
  - 저자 결론: "30명 미만이면 실내에서 잘 동작한다."
- 확장 실험에서 수정한 방법은 오차 2 미만이 50%를 넘었다. 원래 방법은 오차 2 이상이 70%를 넘었고, 22명이 넘으면 오차가 커졌다.
- 실내 대 실외: 실내는 오차 2명 미만이 98% 이상이었다. 실외는 약 70%에서 오차가 2명이었다.
- 대상은 **움직이는 사람만**이다. 걷는 속도가 섞이면 오차가 커진다고 썼다.

### Device-Free Crowd Counting Using Multi-Link Wi-Fi CSI Descriptors in Doppler Spectrum, Electronics 2021 (Brena 외)
- 링크: https://www.mdpi.com/2079-9292/10/3/315
- 데이터는 Di Domenico 외(WiMob 2016)의 공개 데이터셋이다. 안테나 2개 AP → 안테나 3개 Intel 5300으로 링크 6개, 서브캐리어 30개.
  - 비어 있음, 1~8명. 사람들은 자유롭게 움직였다.
  - 방 3곳: 5×6m, 5×9m, 6×12.5m
- 결과: 링크 1개면 44%, 링크 6개면 99% 이상. 방마다 5-fold로 따로 학습했고, 방 사이 이전 실험은 아니다.
- 표 11의 다른 논문 수치는 **[2차 인용]**이다: Di Domenico 0.81(최대 8명), Liu(WiCount) 0.82(5명), Zou(FreeCount) 0.96(7명).
- 원 논문 Di Domenico 2016은 초록만 확인했다(https://www.peco602.com/publication/0020-trained-once-doppler-spectrum/). "한 번 학습하면 다른 방에서도 재학습 없이" 쓸 수 있다고 주장하고 방 2곳 결과를 냈다고 하지만, 숫자는 본문을 못 열어서 확인하지 못했다.

### Fast and Robust Stationary Crowd Counting with Commodity WiFi, IEEE JSAS 2025 (Torun, Parsay, Mostofi)
- 링크: https://arxiv.org/abs/2507.14309 , https://doi.org/10.1109/jsas.2025.3648956
- 앉아 있는 사람들을 센다. 사람이 몸을 꼼지락거리면 신호 대역폭이 변하는데, 그 분포를 모델로 만든다.
  - 하드웨어는 Intel 5300 노트북 2대(내장 안테나)이고 서로 0.5m 떨어져 있다.
  - 모델은 온라인 영상에서 뽑은 움직임으로 만들었고, 현장 CSI로 학습하지 않는다.
- 사무실(최대 5명)과 회의실(최대 13명)에서 실험 42번. 평균 절대오차 1.04명, 수렴까지 평균 51초.
  - 근처를 걸어 다니는 사람 같은 이상 동작을 걸러내는 모듈을 끄면 오차가 1.45로 커진다.
- 인원 수별 표(Table I)가 있지만 HTML을 텍스트로 바꾸면 칸 대응이 깨져서 인원별 숫자는 옮기지 않았다.
- 저자들은 기존 Wi-Fi 인원 추정 연구가 대부분 움직이는 사람 대상이고, 대부분 최대 5명 정도라 사실상 "다인 카운팅"이라고 지적했다.

### 초록만 확인한 것
- WiCount: A Deep Learning Approach for Crowd Counting Using WiFi Signals (Liu 외, ISPA/IUCC 2017), https://doi.org/10.1109/ISPA/IUCC.2017.00148 . 상용 Wi-Fi로 최대 5명, 82.3%.
- FreeCount: Device-Free Crowd Counting with Commodity WiFi (Zou 외, GLOBECOM 2017), https://doi.org/10.1109/GLOCOM.2017.8255034 . 공유기 OpenWrt CSI로 수집하고, 정보이론으로 특징을 고르고, 커널 전이학습(TKL)을 쓴다. 중간 크기 방에서 96%이고 "시간·환경 변화에도 일관"되었다고 한다. 최대 7명과 7명 클래스 81.8%는 Brena 2021 표와 Jamal 2025 표에 인용된 **[2차 인용]** 수치다.
- Device-free crowd counting with WiFi CSI and deep neural networks (Rui Zhou 외, Wireless Networks 2020), https://doi.org/10.1007/s11276-020-02274-7 . Tx·Rx 1쌍. 6명 규모에서는 오차 1명 이내 100%, 34명 규모에서는 1명 이내 97.7%, 2명 이내 99.3%. 본문이 막혀 있어 ACM DL 초록(검색 결과 화면)으로만 확인했다.
- DeepCount (arXiv 1903.05316): Tx 안테나 2 / Rx 안테나 3, 최대 5명, 86.4%. 출입 이벤트로 보정하면 90%.

### 다인 포즈 데이터셋의 인원(질문 c)
- Person-in-WiFi 3D (CVPR 2024): 최대 3명. 인원이 늘면 MPJPE가 91.7 → 108.1 → 125.3mm로 커진다. 라벨링 도구(Kinect SDK)가 인원 상한을 정한다(1부 1-7 참고).
- MM-Fi (NeurIPS 2023): **한 사람만** 있다. 논문 6절에 "3m 거리, 같은 방향, 한 사람으로 통제된 조건이며 다인은 MM-Fi 2.0에서 계획"이라고 썼다. 따라서 인원 추정 학습에는 쓸 수 없다.

### 확인했지만 표에서 뺀 것
- figshare "Room-Level Occupancy Estimation via Wi-Fi CSI on ESP32 Nodes"(데이터셋 34809009): 검색 결과에는 250시간·다구역이라고 나오지만 페이지가 403으로 막혔다. 짝이 되는 논문도 찾지 못했다. **미검증이라 제외했다.**
- arXiv 2601.02177 (ESP32 다인 보행 식별 실패 분석): 인원 추정이 주제가 아니어서 제외했다.

## 2-3. WaveSense(ESP32, Tx 1 + Rx 3, 2×2 구역)에서 현실적인 기대치

1. **가장 가까운 근거는 Wi-CaL**이다(ESP32 링크 4개, 4구역).
   - 걷는 사람 5명까지 날을 바꿔도 중앙값 오차 0.35명이었지만, 오차가 1명 이내인 비율이 약 90%였다. 정확한 인원을 매번 맞히지는 못한다.
   - 우리 Rx 3대는 링크 3개라서 이보다 조금 불리할 수 있다. Brena 결과(링크 1개 44% → 6개 99%)처럼 링크 수가 성능을 크게 좌우한다.
2. **안테나 1개 ESP32 한 대로는 0~3명 정도가 공개 근거의 끝이다**(WiCount 데이터셋, 94%. 방 1곳, 대형 모델 기준).
3. **보안용 권장 출력은 "0명 / 1명 / 2명 이상"이고, 여유가 있으면 "3명 이상"까지다.**
   - 근거: 사람 있음/없음은 여러 논문에서 거의 100%였다.
   - Jamal 논문은 0 / 1 / 2명 이상 세 구간을 각각 99% 이상으로 구분했다(단, 2×2 MIMO NIC 기준).
   - 정확한 인원은 소규모(3~5명)에서만 "±1명" 수준으로 기대하는 게 맞다.
4. **가만히 있는 사람은 따로 문제다.**
   - 대부분 논문이 움직이는 사람 기준이다. Frog Eye는 대상을 아예 "moving people"로 정의했다.
   - 숨어서 가만히 있는 침입자나 앉아 있는 사람은 인원이 적게 세어질 수 있다.
   - Mostofi 그룹의 정지 인원 추정도 Intel 5300과 약 51초 관찰이 필요했고 평균 1명쯤 틀렸다.
   - 그래서 보안 이벤트는 "움직임 감지 → 사람 있음 유지"하는 상태 머신으로 처리하는 게 안전하다.
5. **현장이 바뀌면 다시 보정해야 한다.** ESP32 논문 중 다른 방으로 옮겨 검증한 결과가 있는 것은 없다. Wi-CaL은 날만 바뀌어도 오차가 늘었다. 설치할 때마다 빈 방과 1명, 2명 이상 데이터를 짧게라도 모아서 보정하는 절차가 필요하다.
6. **구역별로 나누기**: 구역(2×2)과 인원을 함께 출력할 수 있다는 근거는 Wi-CaL이다(구역 정확도 91~98%). 하지만 그 결과는 한 무리가 한 구역에 모여 있는 경우만 해당한다. 여러 구역에 사람이 흩어져 있으면 아직 근거가 없다.
7. **수십 명 규모**(Frog Eye 30명, Zhou 34명)는 Intel NIC를 쓰고 홀이나 넓은 공간에서 움직이는 군중을 대상으로 한 결과다. 우리 방 크기와 보안 용도에는 해당하지 않는다. Frog Eye도 15명이 넘으면 오차가 약 2명, 20명이 넘으면 지표가 포화했다.

---

# 3부. 학습 때 없던 사람(침입자)에서 성능이 얼마나 떨어지나: cross-subject 문헌 (2026-11-18 추가)

질문: 우리 방에서 학습한 뒤 처음 보는 사람이 들어오면 어떻게 되나? 침입자는 늘 학습 데이터에 없던 사람이다.

표기 원칙:
- 각 출처는 이번에 직접 열었고, 숫자는 원문 그대로 옮겼다.
- **[초록만]** 본문을 못 열었다. **[슬라이드]** 저자 발표 자료로만 확인했다. **[미확인]** 검증하지 못했다.
- 지표가 서로 달라서 논문끼리 숫자를 직접 비교하면 안 된다.
  - MPJPE/PA-MPJPE: 관절 위치 오차(mm), 낮을수록 좋다. PA-MPJPE는 위치·크기·회전을 맞춘 뒤 잰 값이다.
  - Acc/F1: 정확도(%), 높을수록 좋다.

## 3-1. 요약 표

| 논문 | 과제 / 하드웨어 | 지표 | 같은 사람 | 처음 보는 사람 | 처음 보는 방 | 사람 vs 방 |
|---|---|---|---|---|---|---|
| MM-Fi (NeurIPS 2023) | 3D 포즈. TP-Link N750 2대(Atheros), Tx 안테나 1 / Rx 안테나 3. 모델은 MetaFi++ | MPJPE / PA-MPJPE (프로토콜 1) | 무작위 분할 186.9 / 120.7 | 32명 학습, 8명 테스트: 222.3 / 125.4 | 367.8 / 121.0 | 방이 훨씬 나쁨 |
| Person-in-WiFi 3D (CVPR 2024) | 다인 3D 포즈. Intel 5300 Tx 1 + Rx 3, 7명 | MPJPE | 107.2 (전체 모델) | 한 명씩 빼고: 131.6 | 장소 하나씩 빼고: 626.4 | 방이 훨씬 나쁨 |
| WiPose (MobiCom 2020) | 3D 포즈. Intel 5300 Tx 1, 수신 안테나 9, VICON 라벨, 10명 | 관절 평균 오차(mm) | CSI 28.3 / 3DVP 36.7 | 키 작은 2명 테스트: CSI 103.6 / 3DVP 85.8 | 같은 방 설정만 바꿈: CSI 95.2~121.6 / 3DVP 61.2~87.7 | 비슷한 규모 |
| CSI-Bench (NeurIPS 2025 D&B) | 활동 5종(실생활, 가정 6곳, 6명). 상용 기기 혼합(ESP32-S3 1×1 포함) | Acc | 같은 분포 88.06 (multi-task Transformer) | 54.72 (ViT 최고 59.00) | 54.92 (ViT 58.87) | 거의 같음 |
| Malik 외 (IEEE Access 2026) | 활동 7종(넘어짐·눕기·앉기·서기·걷기 포함). CSI-HAR: RPi4+Nexmon, 3명. 모델은 classic ESP32에서 실행 | Acc | 무작위 분할 96.4 (32채널 tiny CNN) | 사람 하나씩 빼고: 63.1. 모델 6개 평균 29.4%p 하락 | 해당 없음 | 해당 없음 |
| 같은 논문, CSI-Bench 4클래스(35명) | 동일 | Acc | 93.3 | 62.6 | 해당 없음 | 해당 없음 |
| Varga & Cao (Signals 2025) | 활동 7종. CSI-HAR(RPi4+Nexmon, 3명) | Acc / F1 | 0.929 / 0.928 | 2명 학습, 1명 테스트: 0.607 / 0.604 | 해당 없음 | 해당 없음 |
| Elkelany 외 (AICS 2024) | 활동 6종. GJWiFi(1×3 안테나, 서브캐리어 30, 10명) | F1 | 10-fold 99.40 | 사람 하나씩 빼고: 94.92 (방별 96.24 / 95.75 / 92.77) | 별도 실험 없음 | 해당 없음 |
| 같은 논문, OPERAnet | 활동. LOS / NLOS | F1 | hold-out LOS 95.59 / NLOS 93.78 | LOS 92.44 / NLOS 90.64 | 해당 없음 | 해당 없음 |
| XAI2CSI (arXiv 2026) | 활동 5종 + 빈 방. 802.11ax 1×4 SIMO, 수신 노드 3개, 3명, 방 3곳 | Acc | 전체로 학습 88~98% | 최대 65% | 28%를 넘지 못함 | 방이 훨씬 나쁨 |
| DGSense (arXiv 2025) | **손동작** 6종. Intel 5300 3×3, 6명, 방 4곳 | Acc | 97.8 | 83.3 (1명 뺌), 80.6 (2명 뺌) | 81.7 (새 사람 + 새 방은 80.6) | 비슷함. 일반화 기법이 없으면 약 25% vs 약 20% |
| WiPure (Symmetry 2026) **[초록만]** | 활동 5종, 5명, 방 2곳. 하드웨어 미확인 | Acc | 간섭이 있는 조건 95.4 / 91.8 | 82.6±1.7 | 78.5 / 76.0 | 방이 조금 나쁨 |
| Bayad 외 (MeMeA 2025) **[초록만]** | 넘어짐 감지, 2D-CNN | Acc | 최대 100 | 79 | 87 | **사람이 더 나쁨** |
| Widar3.0 (MobiSys 2019 / TPAMI) **[초록+슬라이드]** | 손동작 6종, 16명 | Acc | 92.7 | 학습 인원 1명 → 7명이면 74% → 89% | 92.4 | 해당 없음 |

인원 추정이나 존재 감지를 처음 보는 사람으로 검증한 논문은 **못 찾았다**. 2부의 Wi-CaL, Jamal, WiCount는 모두 사람별로 분할하지 않았다. 간접 근거만 있다:
- XAI2CSI: 사람이 바뀌면 진폭이나 위상 하나만 쓴 모델이 "빈 방"을 자주 틀렸다. 둘을 합친 모델은 빈 방을 거의 완벽하게 맞혔다.
- CSI-Bench: 거리 4단계 분류가 같은 분포 86.41%에서 처음 보는 사람 30.26%로 떨어졌다.

## 3-2. 논문별 상세

### MM-Fi (NeurIPS 2023 D&B), https://arxiv.org/abs/2305.10345
- 분할 방식:
  - S1: 무작위 3:1
  - S2: 사람 기준. 32명 학습, 8명 테스트
  - S3: 환경 기준. 3곳 학습, 1곳 테스트
- WiFi 모델은 MetaFi++다. 본문: "We employ the data processing and model from MetaFi++".
- Table 3, WiFi, MPJPE / PA-MPJPE (mm):

| 분할 | 프로토콜 1 | 프로토콜 2 | 프로토콜 3 |
|---|---|---|---|
| S1 | 186.9 / 120.7 | 213.5 / 121.4 | 197.1 / 121.2 |
| S2 | 222.3 / 125.4 | 247.0 / 122.7 | 231.1 / 124.0 |
| S3 | 367.8 / 121.0 | 360.2 / 117.2 | 369.5 / 116.0 |

- 본문 인용: "the 3D HPE model via WiFi CSI shows a significant decline in performance ... restricting the model's generalization ability across different subjects."
- 비교: LiDAR와 mmWave는 S2에서 PA-MPJPE 변화가 3mm 이내였다.
- 해석: 사람이 바뀌면 MPJPE가 약 +35mm 늘고, 방이 바뀌면 약 +180mm 는다. PA-MPJPE는 S3에서 거의 그대로라서, 새 방에서 생기는 오차는 대부분 위치·크기 쪽이라고 읽힌다.

### Person-in-WiFi 3D (CVPR 2024), https://openaccess.thecvf.com/content/CVPR2024/papers/Yan_Person-in-WiFi_3D_End-to-End_Multi-Person_3D_Pose_Estimation_with_Wi-Fi_CVPR_2024_paper.pdf
- 참가자 7명. 키 160~177cm, 체중 55~70kg으로 **다양성이 좁다**. 장소 3곳(사무실·강의실·복도), 동작 8종.
- Table 8, MPJPE:
  - 한 명씩 빼고 검증(Cross-Person): 131.6 (수평 76.1 / 수직 57.4 / 깊이 62.2)
  - 장소 하나씩 빼고 검증(Cross-Environment): 626.4
- 같은 조건의 전체 모델(진폭 + 잡음 제거한 위상)은 Table 7 기준 107.2다.
- 저자 해석: 사람이 바뀌어도 "effectively recognizes poses despite individual differences in body shape and movement habits". 장소가 바뀌면 "a large decline".

### WiPose (MobiCom 2020), https://wenjunjiang.github.io/MobiCom2020.pdf
- 참가자 10명. 기본 평가는 동작마다 앞 70% 시간을 학습, 뒤 30%를 테스트로 썼다. 같은 사람이 양쪽에 다 들어가고 시간상 붙어 있어서 낙관적이다.
- Table 1, 같은 사람: WiPose(CSI) 28.3mm, WiPose(3DVP) 36.7mm. 비교 모델 RFPose3D는 43.6 / 76.7.
- Table 7, 처음 보는 사람: CSI 103.6 / 3DVP 85.8. RFPose3D는 141.7 / 138.8.
  - 테스트한 2명은 다른 사람들보다 키가 작았다. 저자도 "This makes the testing set quite biased"라고 썼다.
- 같은 방에서 설정만 바꾼 결과(1부 1-3 참고)는 CSI 95.3 / 121.6 / 95.2, 3DVP 61.2 / 79.1 / 87.7이다.
- 해석: 사람이 바뀌어 커진 오차(약 3.7배)가 방 설정 변화와 비슷한 규모다. 저자들은 뼈 길이 같은 골격 정보를 모델에 넣어 사람 간 차이를 줄였다고 주장한다.

### MetaFi++ (IEEE IoT-J 2023), https://doi.org/10.1109/jiot.2023.3262940 **[초록만]**
- 원 논문은 PCK@50 97.30%를 보고했다(초록).
- 처음 보는 사람 결과는 원 논문에서 확인하지 못했다. 위 MM-Fi 실험의 S2가 사실상 MetaFi++를 처음 보는 사람으로 평가한 결과다.

### CSI-Bench (NeurIPS 2025 Datasets & Benchmarks), https://arxiv.org/abs/2505.21866
- 상용 라우터와 IoT 기기를 썼다(1×1~2×2, 1×4). ESP32-S3는 1×1, 2.4GHz 20MHz에서 서브캐리어 64개다.
- 다중 과제 데이터셋은 6명, 가정 6곳, 기기 11대다. 활동은 걷기(거리 4단계), 뛰기, 점프, 앉아서 숨쉬기, 손 흔들기.
- Table 4, 같은 분포 활동 정확도: 과제별로 따로 학습 75.40%, 다중 과제로 함께 학습 88.06%.
- Table 5, 다중 과제 Transformer:

| 과제 | 다른 기기 | 다른 환경 | 다른 사람 |
|---|---|---|---|
| 활동 Acc | 61.82 | 54.92 | 54.72 |
| 거리(proximity) Acc | 30.68 | 29.67 | 30.26 (같은 분포는 86.41) |

- Table 13, 활동 분류 모델별 처음 보는 사람 Acc: ViT 59.00, ResNet18 59.24, LSTM 53.33. 다른 환경도 54~59로 비슷하다.

### Malik, Ahmad, Kim, IEEE Access 2026, https://doi.org/10.1109/ACCESS.2026.3742666 (CC BY)
- 모델은 classic ESP32-WROOM-32(외장 메모리 없음)에서 직접 돌렸다. 처음 보는 사람 실험에 쓴 데이터는 다음 두 가지다.
  - CSI-HAR: RPi4 + Nexmon, 3명, 7종. 굽히기·넘어짐·눕기·뛰기·앉기·일어서기·걷기
  - CSI-Bench: 35명, 4클래스
- CSI-HAR, 무작위 분할 → 한 명씩 빼고 검증(Table 15):
  - 32채널 tiny CNN 96.4% → 63.1%, Random Forest 83.1% → 58.1%
  - "Every model loses 25–33 percentage points ... mean decrease of 29.4 points."
- 처음 보는 사람에서 넘어짐 재현율은 "approximately 38%"였다. 일어서기와 앉기는 둘 다 정지 자세로 끝나서 서로 헷갈렸다.
- CSI-Bench(Table 16): tiny CNN 93.3% → 62.6%, Random Forest 84.1% → 51.7%.
- ESP32 실측: 한 사람을 두 세션 측정했다. 세션 안에서는 46.9%, 세션을 바꾸면 25.8%였다. 사람 간 실험이 아니라 같은 사람의 세션 간 하락이다.
- 저자 결론: "recognizing new people is a bigger problem than fitting the model in memory."

### Varga & Cao, Signals 6(4):59, 2025, https://www.mdpi.com/2624-6120/6/4/59
- 다른 논문(Shahverdi 외)을 다시 구현했다. 데이터는 CSI-HAR(RPi4 + Nexmon, TP-Link Archer C20, 5GHz 20MHz, 3명, 7종).
- Table 3:
  - 원 논문 보고: 0.92 / 0.92
  - 사람 구분 없이 재학습: 0.929 / 0.928
  - 사람 기준으로 분할(2명 학습, 1명 테스트): **0.607 / 0.604**
- 핵심 주장: 무작위 분할은 "re-identify participants"를 측정할 뿐이다. 데이터가 새어 들어가 성능이 부풀려진다.

### Elkelany, Ross, Mckeever, AICS 2024 (CEUR Vol-3910), https://ceur-ws.org/Vol-3910/aics2024_p78.pdf
- GJWiFi: 10명, 활동 6종(움직임 없음, 앉기/일어서기, 걷기, 돌기, 펜 줍기 등). 패킷마다 1 Tx × 3 Rx 안테나 × 서브캐리어 30. 환경 3곳(E1 실험실, E2 복도, E3 NLOS).
- F1:
  - hold-out: 97.67 / 98.24 / 96.36 (평균 97.42)
  - 10-fold: 평균 99.40
  - 사람 하나씩 빼고: 96.24 / 95.75 / 92.77 (평균 94.92)
- OPERAnet F1:
  - LOS: hold-out 97.19 / 93.98 (평균 95.59) → 사람 하나씩 빼고 93.10 / 91.78 (평균 92.44)
  - NLOS: hold-out 평균 93.78 → 사람 하나씩 빼고 91.23 / 90.04 (평균 90.64)
- 하락폭이 3~5%p로 작다. 참가자가 10명으로 비교적 많고, 각 환경 안에서만 평가했다.

### XAI2CSI (arXiv 2608.31034, 2026-08), https://arxiv.org/abs/2608.31034
- 802.11ax 5GHz, 150Hz, 1×4 SIMO, 수신 노드 3개. 3명, 방 3곳(Lab/Office/Hall), 이틀.
- 클래스: 빈 방·점프·뛰기·앉기·걷기.
- 수치는 그림에서 나온 것이라 본문에 적힌 값만 옮긴다:
  - 모든 조건으로 학습한 모델(상한): "88-98%"
  - 처음 보는 사람: "drops to at most 65%"
  - 처음 보는 방: "not exceeding 28%"
- 처음 보는 사람에서 진폭이나 위상 하나만 쓴 모델은 "frequently misclassifies Empty"했다. 둘을 합친 모델은 빈 방을 "near-perfect accuracy"로 맞혔다. 앉기와 뛰기는 여전히 어려웠다.

### DGSense (arXiv 2502.08155), https://arxiv.org/abs/2502.08155
- **WiFi 실험은 손동작**이다(Intel 5300 노트북 2대, 각각 안테나 3개, 링크 9개). 같은 논문의 넘어짐 실험(새 사람 95.0%)은 **음향 기반이라 제외**했다.
- 결과:
  - 같은 사람, 본 방에서 5-fold: 97.8%
  - 처음 보는 사람: 83.3%(5명 학습, 1명 테스트), 80.6%(4명 학습, 2명 테스트)
  - 처음 보는 방: 81.7%
  - 처음 보는 사람 + 처음 보는 방: 80.6%
- 이 방법 없이 학습하면 처음 보는 사람은 "around 25%", 처음 보는 방은 "around 20%"였다.

### 초록이나 슬라이드로만 확인한 것
- **WiPure** (Symmetry 18(10):1701, 2026), https://www.mdpi.com/2073-8994/18/10/1701 **[초록만]**
  - 간섭이 있는 조건에서 95.4±0.7% / 91.8±1.1%, 사람 하나씩 빼고 5-fold 82.6±1.7%, 미세조정 없이 다른 환경 78.5±1.8% / 76.0±2.3%.
  - 하드웨어는 확인하지 못했다. 인접 안테나 위상차를 쓰므로 다중 안테나다.
- **Bayad 외, "Adaptive Fall Detection Using WiFi CSI for Unseen Environments and New Individuals"** (IEEE MeMeA 2025), https://doi.org/10.1109/MeMeA65319.2025.11068083 **[초록만]**
  - 같은 환경 최대 100%, 처음 보는 환경 87%, 처음 보는 사람 79%. 데이터 증강으로 13% 개선했다.
- **Widar3.0** (MobiSys 2019, TPAMI 2022) **[초록+저자 슬라이드]**
  - 슬라이드: https://tns.thss.tsinghua.edu.cn/~yangzheng/papers/Widar3-MobiSys-Slides.pdf
  - 같은 조건 92.7%. 다른 조건에서는 위치 89.7%, 방향 82.6%, 환경 92.4%(슬라이드 순서 기준).
  - 슬라이드에 "The accuracy increases from 74% to 89% when the number of training users varies from 1 to 7"이라고 나온다. 인원이 늘면 테스트한 사람과의 행동 차이가 줄어든다는 설명이 붙어 있다.
  - 본문 PDF는 막혀서 열지 못했다.
- DT-Pose나 HPE-Li의 MM-Fi 처음 보는 사람 수치는 리더보드 사이트에서만 봐서 넣지 않았다 **[미확인]**.

## 3-3. 사람이 바뀔 때 vs 방이 바뀔 때
- **포즈 회귀**에서는 방이 바뀔 때가 훨씬 나쁘다.
  - MM-Fi: MPJPE +35mm vs +181mm
  - Person-in-WiFi 3D: 131.6 vs 626.4
  - 단, WiPose는 사람이 바뀐 하락이 방 설정을 바꾼 하락과 비슷했다.
- **활동 분류**에서는 둘이 비슷하거나, 사람 쪽 하락도 크다.
  - CSI-Bench: 54.72 vs 54.92
  - DGSense: 83.3 vs 81.7
  - WiPure: 82.6 vs 76~78.5
  - XAI2CSI는 방이 훨씬 나빴다(65% vs 28%).
  - MeMeA 넘어짐 감지는 사람이 더 나빴다(79% vs 87%, 초록).
- 사람 하락폭은 **학습 인원 수와 다양성**에 크게 좌우된다.
  - 3명짜리 데이터에서는 25~33%p 떨어졌다(Malik, Varga).
  - 10명짜리 GJWiFi에서는 3~5%p였다(Elkelany).
  - Widar3.0 슬라이드: 학습 인원 1명 → 7명이면 74% → 89%.
- **우리는 방이 고정**이라 가장 큰 하락 요인(방)은 빠진다. 남는 위험은 처음 보는 사람, 그리고 날·세션 변화다. 세션 변화도 Malik의 ESP32 실측에서 46.9% → 25.8%로 컸다.

## 3-4. WaveSense(ESP32-C5, Tx 1 + Rx 3, 한 방 보정)에 주는 의미

ESP32-C5로 처음 보는 사람을 평가한 논문은 없다. 아래는 위 결과에서 추론한 것이다.

### 보정 인원과 다양성
- 최소 **8~10명**, 가능하면 **15명 이상**을 권한다.
  - 근거: 하락폭이 작았던 GJWiFi가 10명이었다. Widar3.0에서는 7명까지 늘리는 동안 계속 올랐다. MM-Fi는 32명을 학습에 썼다.
- 키, 체형(마른/큰 체격), 성별, 옷차림(두꺼운 겉옷·가방 포함), 걷는 속도를 고르게 섞는다.
  - Person-in-WiFi 3D(키 160~177cm)와 WiPose(키 작은 사람으로 테스트)는 다양성이 좁으면 처음 보는 사람에게 약하다는 걸 보여 준다.
- 한 사람당 여러 날, 여러 세션을 녹화한다. 세션 하나만 있으면 사람 효과와 세션 효과가 섞인다.
- 빈 방 녹화를 시간대별로 충분히 모은다. 사람 없이 생기는 움직임(선풍기, 커튼, 문)도 "사람 없음" 쪽으로 넣는다.

### 처음 보는 사람으로 평가하는 법
- 무작위 창 분할은 쓰지 않는다. 창이 겹치면 같은 사람·같은 순간이 학습과 테스트 양쪽에 들어간다. Varga 결과는 0.929 vs 0.607이었다.
- **사람 하나씩 빼고 검증(LOSO)**을 하거나, 사람 단위로 묶어서 k-fold를 한다. 같은 사람의 다른 세션이 학습에 섞이지 않게 한다.
- 가능하면 **사람과 날짜를 둘 다 뺀** 테스트를 하나 더 만든다. 보정에 전혀 참여하지 않은 2~3명을 최종 시험용으로 따로 둔다.
- 평균만 보지 말고 **사람별 점수와 최저 점수**를 같이 보고한다. Malik도 "A single average would hide these differences"라고 썼다.
- 보안 용도이므로 정확도보다 **빈 방에서의 오탐률**과 **사람이 있는데 못 잡는 비율**을 따로 잰다.

### 처음 보는 침입자에 대해 현실적인 기대치
- **존재(있음/없음)**: 가장 유망하다.
  - 근거: 같은 사람 기준으로는 여러 논문에서 거의 100%였고(2부 Jamal), XAI2CSI는 진폭과 위상을 합치면 처음 보는 사람에서도 빈 방을 거의 완벽하게 맞혔다.
  - 단, 처음 보는 사람으로 존재 감지만 따로 수치화한 논문은 못 찾았다. 우리가 직접 사람을 빼고 검증해야 한다.
  - 가만히 있는 사람은 따로 확인이 필요하다.
- **인원(0 / 1 / 2명 이상)**: 처음 보는 사람 근거가 없다.
  - 같은 사람 기준 결과(Wi-CaL에서 오차 1명 이내 약 90%)보다는 떨어질 거라고 가정해야 한다.
  - 보정 인원을 다양하게 모으고, 처음 보는 사람 조합으로 "1명 vs 2명 이상"을 따로 검증해야 한다.
- **자세(서기 / 앉기 / 눕기 / 걷기 / 넘어짐)**: 처음 보는 사람에서는 **55~65% 수준**이 문헌상 현실치다.
  - 근거: 클래스 4~7개 기준 CSI-Bench 54.7~59.0%, CSI-HAR 60.7~63.1%, CSI-Bench 4클래스 62.6%.
  - 넘어짐 재현율은 약 38%까지 떨어진 사례가 있다(Malik).
  - 그래서 보안 경보는 "움직임 / 정지"나 "서 있음 / 바닥 근처" 같은 거친 단계로 두는 게 맞다. 자세 라벨은 참고 정보로만 쓴다.
  - 참가자를 10명 이상으로 늘리면 하락폭이 3~5%p 수준까지 줄어든 사례(Elkelany)도 있다. 우리 목표는 그쪽이다.


# 4부. 가상/증강 데이터로 처음 보는 사람 성능을 얼마나 올릴 수 있나 (2026-11-19 추가)

출처 확인 수준: 검색 요약과 본문 발췌만 봄. 전문 정독 전이라 수치는 재확인 필요.

| 연구 | 방식 | 처음 보는 사람/환경 개선폭 |
|---|---|---|
| CM-GR (PMC12473887, 2025), https://pmc.ncbi.nlm.nih.gov/articles/PMC12473887/ | 비전 스켈레톤을 조건으로 사람별 가상 CSI 생성 | cross-subject 제스처 최대 +10.26%p (MM-Fi), +9.5%p (자체셋). 환경/위치 평균 +9.29%p |
| RFBoost (arXiv 2410.07230), https://arxiv.org/abs/2410.07230 | 물리 기반 증강 | cross-person 평균 +0.87%p, cross-room +1.1%p, cross-Rx +3.6~5.4%p |
| Strohmayer & Kampel (arXiv 2401.00964, TU Wien, ESP32 계열), https://arxiv.org/pdf/2401.00964 | 이미지식 단순 증강 (circular rotation, resized crop, amplitude) | LOS에서 NLOS로 최대 +22.5%p, 안테나 시스템 간 +18.5~21.1%p. 조합에 따라 오히려 떨어지기도 함 |
| MockiFi, https://touhidroid.me/assets/pdf/mockifi.pdf | 조건부 신경과정으로 CSI 모방, zero-shot | 처음 보는 사용자 활동 정확도 68.3~83.2% (베이스라인 대비 개선폭은 미확인) |

요약
- 사람이 바뀌는 문제에는 단순 증강 효과가 작음 (RFBoost +0.87%p). 사람별 가상 생성(CM-GR)이 약 +10%p로 가장 큼.
- 단순 증강은 방/장비가 바뀔 때 더 잘 먹힘 (+15~22%p). 같은 TU Wien 그룹이라 우리 ESP32 데이터에 바로 적용해볼 만함.
- CM-GR처럼 웹캠 스켈레톤으로 가상 CSI를 만드는 구조는 우리 셋업(웹캠을 라벨용으로 이미 씀)과 맞음.
- 결론: 가상 데이터는 실측 인원 부족을 약 10%p 정도 메우는 수준. 3부 결론(실측 8~10명 + 사람 단위 검증)은 그대로 유지.

## 부록: 외장안테나(-1U) 보드 가격 (2026-11-19 조회)
- 공식 ESP32-C5-DevKitC-1-N8R8: PCB 안테나(U.FL 없음), DigiKey $15
- DFRobot FireBeetle 2 ESP32-C5-U (N4): WROOM-1U, U.FL, $8.40, 동봉 안테나는 2.4GHz 전용 → 겸용 안테나 별도 필요 https://www.dfrobot.com/product-3144.html
- UeeKKoo ESP32-C5 WROOM-1U N32R8: U.FL + 2.4/5GHz 겸용 안테나 포함, Amazon 약 $20 https://www.amazon.com/dp/B0GY94RVJG
- 모듈 단품 ESP32-C5-WROOM-1U-N8R8: Mouser EU €4.70 (보드 직접 설계·납땜 필요)
