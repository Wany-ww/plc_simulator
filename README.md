# 미쓰비시 PLC CPU 시뮬레이터 (MELSEC TCP)

미쓰비시 PLC(Q 시리즈, iQ-R 시리즈 등)의 CPU를 소프트웨어적으로 에뮬레이션하여, 상위 시스템(SCADA, MES, 커스텀 앱 등)이 MC 프로토콜(TCP/IP)을 통해 데이터 읽기/쓰기를 테스트할 수 있는 환경을 제공하는 시뮬레이터입니다.

## 🚀 주요 기능

- **다중 PLC 인스턴스 관리**: 서로 다른 포트에서 여러 대의 시뮬레이터를 동시에 실행 및 제어 가능.
- **MC 프로토콜 지원**: 표준 MC 프로토콜 3E/4E 프레임(바이너리) 기반의 Batch Read/Write 지원.

- **디바이스 데이터 모니터링**: D-레지스터(D0 ~ D65535) 데이터를 웹 UI를 통해 실시간으로 확인 및 수정.
- **Python 스크립팅 엔진**: 사용자가 작성한 Python 코드를 주기적으로 실행하여 디바이스 데이터를 동적으로 업데이트.
- **현대적인 Web GUI**: Glassmorphism 디자인이 적용된 다크 모드 UI와 Monaco Editor 기반의 스크립트 편집기 제공.
- **통신 장애 시뮬레이션**: 설정된 확률과 주기에 따라 강제 연결 해제 이벤트를 발생시켜 상위 시스템의 예외 처리 테스트 가능.

## 🛠 기술 스택

- **Backend**: Python 3.x, FastAPI, asyncio, WebSockets
- **Frontend**: Vanilla HTML5, CSS3 (Modern UI), JavaScript
- **Editor**: Monaco Editor (via CDN)

## 📂 프로젝트 구조

```text
plc_simulator/
├── data/               # 설정 및 스크립트 저장소
├── simulator/          # PLC 에뮬레이션 핵심 로직
│   ├── mc_protocol.py  # MC 프로토콜 파서
│   └── plc.py          # PLC 인스턴스 및 스크립트 엔진
├── static/             # 프론트엔드 자원 (HTML, CSS, JS)
├── main.py             # FastAPI 엔트리 포인트
└── requirements.txt    # 의존성 목록
```

## ⚙️ 시작하기

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
python main.py
```

### 3. 접속
웹 브라우저에서 `http://localhost:8000`으로 접속합니다.

## 📝 라이선스

이 프로젝트는 학습 및 테스트 목적으로 제작되었습니다.
