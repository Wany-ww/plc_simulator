# 미쓰비시 PLC CPU 시뮬레이터 (MELSEC TCP) 구현 계획

`project_spec.md`에 명시된 요구사항을 바탕으로 다중 PLC 인스턴스를 관리하고, MC 프로토콜(TCP) 통신을 지원하며, Python 스크립트를 통한 동적 데이터 업데이트 및 웹 기반 GUI를 제공하는 시뮬레이터를 개발합니다.

## User Review Required

> [!IMPORTANT]
> **프론트엔드 및 백엔드 기술 스택 선정**
> *   **Backend:** Python 3.x 기반으로 FastAPI를 사용하여 REST API 및 WebSocket 통신을 구현합니다. 비동기(`asyncio`) 처리를 통해 다중 TCP 서버 및 스크립트 실행 스레드를 효율적으로 관리합니다.
> *   **Frontend:** 별도의 복잡한 프레임워크 없이 Vanilla HTML/CSS/JavaScript를 사용하며, 고급스러운 Dark mode / Glassmorphism 스타일의 UI를 구현합니다. 코드 에디터는 Monaco Editor(CDN)를 사용하여 구문 강조 기능을 제공할 예정입니다.
> 
> **이러한 기술 스택이 요구사항에 부합하는지 확인 부탁드립니다.**

## Open Questions

> [!WARNING]
> 1. **MC 프로토콜 프레임 구조:** 3E 프레임(Q 시리즈)과 4E 프레임(iQ-R 시리즈) 중 Binary 방식과 ASCII 방식이 존재합니다. 일반적으로 바이너리 방식이 많이 사용되는데, Binary 방식만 구현해도 될지, 아니면 ASCII 방식도 지원해야 할지 확인 부탁드립니다. (본 계획은 Binary 통신을 기본으로 가정합니다.)
> 2. **D-Register 외 디바이스 지원:** 현재 명세서에는 D-레지스터(D0 ~ D65535)에 대한 일괄 읽기/쓰기(Batch Read/Write)만 명시되어 있습니다. 향후 M, X, Y 등 다른 디바이스 메모리 확장이 고려되어야 하는지 질문드립니다.

## Proposed Changes

### Backend (Python)

#### [NEW] `main.py`
FastAPI 애플리케이션의 진입점. REST API 라우터 설정 및 WebSocket 엔드포인트를 제공하여 프론트엔드와 통신합니다.

#### [NEW] `simulator/manager.py`
다중 PLC 인스턴스를 관리하는 `PlcManager` 클래스. `config.json`을 읽고 저장하며, 개별 PLC 시뮬레이터의 시작, 중지 상태를 관리합니다.

#### [NEW] `simulator/plc.py`
개별 PLC 인스턴스를 나타내는 `PlcSimulator` 클래스.
*   **Memory:** 65536개의 16비트 정수(unsigned short) 배열 관리.
*   **Script Engine:** 파이썬 `exec()` 혹은 독립된 네임스페이스를 통해 사용자가 정의한 스크립트를 주기적으로 실행(asyncio task).
*   **Disconnect Simulation:** 설정된 확률과 주기에 따라 TCP 연결 강제 종료 로직.

#### [NEW] `simulator/mc_protocol.py`
MC 프로토콜 (3E/4E 프레임) 패킷 파싱 및 응답 생성 클래스.
*   TCP 소켓 서버 (asyncio 기반)
*   Batch Read (0401), Batch Write (1401) 명령 처리.

### Frontend (GUI)

#### [NEW] `static/index.html`
단일 페이지 애플리케이션(SPA) 구조의 메인 HTML.
*   **Left Sidebar:** PLC 인스턴스 목록 및 "New PLC" 버튼.
*   **Main View:** 선택된 PLC의 상태(Start/Stop), 설정 편집, D-Register 뷰어(Table), 스크립트 에디터(Monaco).

#### [NEW] `static/style.css`
고품질의 현대적이고 동적인 웹 디자인 적용. (Dark Mode, Glassmorphism, Micro-animations)

#### [NEW] `static/app.js`
프론트엔드 로직 처리.
*   FastAPI 백엔드와의 REST API 통신 (인스턴스 생성/수정/삭제/제어).
*   WebSocket을 통한 실시간 D-Register 데이터 스트리밍 및 업데이트.
*   Monaco Editor 초기화 및 스크립트 저장/적용 기능.

### Configuration & Data

#### [NEW] `data/config.json`
PLC 설정 정보가 저장될 초기 설정 파일.
#### [NEW] `data/scripts/`
각 PLC 인스턴스의 파이썬 스크립트 파일이 저장될 디렉토리.

## Verification Plan

### Automated Tests
*   **MC Protocol Test:** 파이썬으로 작성된 간단한 MC 프로토콜 클라이언트를 구현하여, 로컬에서 구동된 시뮬레이터(포트 5001 등)에 연결해 Batch Read/Write 명령이 정상 작동하는지 테스트합니다.
*   **Script Engine Test:** 스크립트 내에서 `update(plc)`를 통해 변경된 `plc.d[address]` 값이 실제 시뮬레이터 메모리에 반영되고 클라이언트로 읽히는지 검증합니다.

### Manual Verification
*   **GUI 동작:** 웹 브라우저에서 제공된 UI를 통해 PLC 인스턴스를 생성하고, 포트 중복 검사, 시작/정지 동작을 테스트합니다.
*   **실시간 모니터링:** 웹브라우저의 Device Viewer(Table)에서 D-Register 값이 스크립트에 의해 실시간으로 변하는 것을 확인하고, 사용자가 테이블에서 값을 직접 수정했을 때 서버에 잘 반영되는지 확인합니다.
