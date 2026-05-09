제시해주신 요구사항을 바탕으로, \*\*미쓰비시 PLC CPU 시뮬레이터(MELSEC TCP 통신)\*\* 개발을 위한 상세 명세서를 작성하였습니다. 이 문서는 Antigravity가 시스템의 구조, 통신 프로토콜, 스크립팅 엔진 및 GUI 구성을 정확히 이해하고 구현하도록 설계되었습니다.



\---



\# \[명세서] 미쓰비시 PLC CPU 시뮬레이터 (MELSEC TCP)



\## 1. 개요 (Overview)

본 시스템은 미쓰비시 PLC(Q 시리즈, iQ-R 시리즈 등)의 CPU를 소프트웨어적으로 에뮬레이션하여, 상위 시스템(SCADA, MES, 커스텀 앱 등)이 MC 프로토콜(TCP/IP)을 통해 데이터 읽기/쓰기를 테스트할 수 있는 환경을 제공한다. 특히 다중 인스턴스 실행과 Python 기반의 동적 데이터 업데이트 기능을 핵심으로 한다.



\## 2. 주요 기능 (Core Features)



\### 2.1. 다중 PLC 인스턴스 관리

\*   \*\*독립적 설정:\*\* 각 시뮬레이터 인스턴스는 별도의 이름, 포트, 시리즈 설정을 가진다.

\*   \*\*동시 구동:\*\* 여러 대의 시뮬레이터를 서로 다른 포트에서 동시에 활성화 가능.

\*   \*\*PLC 시리즈 선택:\*\* Q 시리즈(3E 프레임), iQ-R 시리즈(4E 프레임 등) 프로토콜 규격 선택 가능.

\*   \*\*통신 장애 시뮬레이션:\*\* 설정된 주기 및 빈도에 따라 강제로 TCP 연결을 끊는(Disconnect) 이벤트 발생 기능.



\### 2.2. 디바이스 데이터 관리 (D-Register)

\*   \*\*메모리 에뮬레이션:\*\* 각 PLC 인스턴스별로 독립적인 D-레지스터 영역(예: D0 \~ D10000)을 메모리에 유지.

\*   \*\*GUI 모니터링:\*\* 현재 D-레지스터의 값을 실시간 표(Table) 형태로 표시.

\*   \*\*값 수정:\*\* GUI 상에서 특정 어드레스의 값을 직접 수정하여 통신 결과 확인 가능.



\### 2.3. Python 스크립트 기반 동적 업데이트

\*   \*\*커스텀 로직 주입:\*\* 사용자가 작성한 Python 코드를 실행하여 D-레지스터 값을 실시간으로 변경.

\*   \*\*스크립트 에디터:\*\* GUI 상에서 직접 코드를 수정하고 적용 가능.

\*   \*\*주기적 실행:\*\* 설정된 밀리초(ms) 단위로 스크립트의 `update` 함수를 호출.



\---



\## 3. 상세 사양 (Technical Specifications)



\### 3.1. 통신 프로토콜 (MC Protocol)

\*   \*\*Protocol:\*\* TCP/IP 기반 MC 프로토콜 (3E/4E 프레임 지원)

\*   \*\*Command 지원:\*\*

&#x20;   \*   Batch Read (D-Register)

&#x20;   \*   Batch Write (D-Register)

&#x20;   \*   Random Read/Write (선택 사항)

\*   \*\*Response:\*\* 미쓰비시 표준 응답 포맷 준수 (정상/에러 코드 반환)



\### 3.2. PLC 인스턴스 설정 항목

| 항목 | 설명 | 예시 |

| :--- | :--- | :--- |

| \*\*Name\*\* | 시뮬레이터 식별자 | `Line1\_PLC` |

| \*\*Series\*\* | 프로토콜 타입 선택 | `Q Series`, `iQ-R Series` |

| \*\*IP Address\*\* | 바인딩할 IP (기본값: 127.0.0.1) | `0.0.0.0` (모든 인터페이스) |

| \*\*Port\*\* | TCP 접속 포트 | `5001`, `5002` |

| \*\*Disconnect Interval\*\* | 연결 유지 시간 (초) | `60` (60초 마다 연결 해제 시도) |

| \*\*Disconnect Frequency\*\* | 연결 해제 확률 (%) | `10` (10% 확률로 끊김 발생) |



\### 3.3. 스크립팅 엔진 (Python Logic)

\*   \*\*Context:\*\* 각 PLC 객체는 자신의 `device\_map`에 접근할 수 있는 `self` 객체를 스크립트에 전달.

\*   \*\*코드 예시:\*\*

&#x20;   ```python

&#x20;   # {PLC\_NAME}\_update\_event.py

&#x20;   import random



&#x20;   def update(plc):

&#x20;       # D1234에 1\~2 사이의 랜덤값 입력

&#x20;       plc.d\[1234] = random.randint(1, 2)

&#x20;       

&#x20;       # D1236에 4\~100 사이의 랜덤값 입력

&#x20;       plc.d\[1236] = random.randint(4, 100)

&#x20;       

&#x20;       # 조건부 로직 예시

&#x20;       if plc.d\[1000] == 1:

&#x20;           plc.d\[1001] += 1

&#x20;   ```



\---



\## 4. 시스템 아키텍처 (Architecture)



1\.  \*\*Backend (Python):\*\*

&#x20;   \*   `TCPServer`: 각 포트별 멀티스레드/비동기 서버 구동.

&#x20;   \*   `Protocol Handler`: MC 프로토콜 패킷 파싱 및 응답 생성.

&#x20;   \*   `Script Runner`: `exec()` 또는 `importlib`을 활용하여 사용자 정의 Python 스크립트 주기적 실행.

2\.  \*\*Frontend (GUI):\*\*

&#x20;   \*   `Instance Manager`: PLC 목록 생성 및 시작/정지 제어.

&#x20;   \*   `Device Viewer`: D-레지스터 그리드 뷰 (Pagination 지원).

&#x20;   \*   `Script Editor`: 구문 강조가 포함된 코드 편집창.



\---



\## 5. 데이터 구조 (Data Structure)



\### 5.1. PLC 설정 정보 (`config.json`)

```json

\[

&#x20; {

&#x20;   "name": "abcd",

&#x20;   "series": "Q",

&#x20;   "port": 5001,

&#x20;   "disconnect\_event": { "interval\_sec": 100, "chance\_percent": 5 },

&#x20;   "script\_path": "./scripts/abcd\_update.py",

&#x20;   "script\_interval\_ms": 500

&#x20; }

]

```



\### 5.2. 메모리 맵

\*   Internal Array: `unsigned short` (16-bit) 배열로 D0 \~ D65535 관리.



\---



\## 6. 작업 흐름 (Workflow)



1\.  \*\*인스턴스 생성:\*\* 사용자가 GUI에서 "New PLC"를 클릭하고 이름, 포트, 시리즈를 설정한다.

2\.  \*\*스크립트 작성:\*\* 해당 PLC에 연결된 Python 스크립트 창에서 `update` 로직을 작성하고 저장한다.

3\.  \*\*시뮬레이터 시작:\*\* "Start" 버튼을 누르면 TCP 서버가 리스닝을 시작하고, 스크립트 엔진이 설정된 주기마다 구동된다.

4\.  \*\*외부 통신:\*\* 실제 PLC와 통신하는 프로그램(Client)이 시뮬레이터 IP/Port로 접속하여 데이터를 읽고 쓴다.

5\.  \*\*모니터링 및 간섭:\*\* 사용자는 GUI의 Device Viewer를 통해 값이 변하는 것을 실시간 확인하고, 필요 시 직접 값을 변경하여 클라이언트 앱의 반응을 테스트한다.



\---



\*\*Antigravity 가이드:\*\*

이 명세서는 미쓰비시 MC 프로토콜의 표준인 3E/4E 프레임을 기반으로 서버를 구현하고, Python의 `threading` 또는 `asyncio`를 사용하여 다중 포트를 처리하는 것을 핵심으로 합니다. 특히 스크립팅 엔진에서 `self.d\[address]` 형태의 직관적인 인터페이스를 제공하는 것이 중요합니다.

