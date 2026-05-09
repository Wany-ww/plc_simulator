# 프로젝트 개발 히스토리 (History)

이 문서는 Antigravity AI와 사용자가 협업하여 미쓰비시 PLC 시뮬레이터를 개발한 과정을 기록합니다.

## 1. 주요 프롬프트 및 요구사항 요약

- **초기 요청**: `project_spec.md` 명세서에 따른 미쓰비시 PLC CPU 시뮬레이터(MELSEC TCP) 전체 구현.
- **주요 기능 요구**:
    - MC 프로토콜(3E/4E 프레임) 지원 및 바이너리 통신.
    - 다중 PLC 인스턴스 관리 (포트 분리, 독립 구동).
    - Python 스크립트 기반의 동적 데이터 업데이트 기능.
    - 실시간 D-Register 모니터링 및 수정을 지원하는 현대적인 웹 GUI (Glassmorphism 적용).
- **Git 관리 요청**:
    - 작업 단계별 이슈(Issue) 및 라벨(Label) 생성.
    - GitHub Actions 워크플로우(CI) 설정.
    - Wiki 및 메인 저장소에 구현 계획서 및 README 업로드.

## 2. 단계별 구현 내용

### Phase 1: 아키텍처 설계 및 계획
- FastAPI(Backend)와 Vanilla JS/CSS(Frontend)를 결합한 비동기 시스템 설계.
- MC 프로토콜 3E 프레임 파서 및 스크립트 엔진 구동 방식 정의.

### Phase 2: 프로젝트 스캐폴딩
- `simulator/`, `static/`, `data/` 등 디렉토리 구조 생성 및 의존성 라이브러리(`requirements.txt`) 설정.

### Phase 3: 백엔드 핵심 로직 (MC Protocol & Memory)
- **`mc_protocol.py`**: 3E 프레임의 Batch Read/Write 명령 파싱 및 응답 로직 구현.
- **`plc.py`**: 65536개의 D-Register 메모리 맵과 Python `exec()` 기반 스크립트 실행 루프 구현.
- **`manager.py`**: 여러 인스턴스의 라이프사이클(시작/정지/설정) 관리 및 설정 저장 기능.

### Phase 4: 프론트엔드 GUI 개발
- **UI Design**: 다크 모드와 Glassmorphism 스타일을 적용한 프리미엄 UI 설계.
- **Interactions**:
    - WebSocket을 통한 실시간 데이터 스트리밍.
    - Monaco Editor를 통합한 실시간 스크립트 편집기.
    - 페이지네이션이 적용된 디바이스 뷰어 및 더블 클릭을 통한 데이터 직접 수정.
    - **String View**: D-Register의 16비트 값을 2글자의 ASCII 문자열로 변환하여 표시하는 컬럼 추가.
    - **Memory Editing Enhancements**: 
        - Hex 컬럼 수정 시 Decimal 대신 Hex 문자열 입력 지원.
        - String 컬럼 더블 클릭 시 직접 문자열(2자)로 데이터 입력 기능 추가.

### Phase 5: GitHub 통합 및 CI/CD
- GitHub REST API를 활용하여 작업 단계별 이슈(Phase 1~6)와 맞춤형 라벨 자동 생성.
- `.github/workflows/ci.yml`을 통한 문법 검사 및 빌드 테스트 자동화.

## 3. 구현 내용 리뷰 및 자가 평가

### ✅ 장점
- **확장성**: `PlcManager`와 `PlcSimulator` 클래스 구조가 명확하여 추후 4E 프레임이나 타 메모리 영역(M, X, Y) 확장이 용이함.
- **사용자 경험(UX)**: Monaco Editor와 실시간 WebSocket 업데이트를 통해 실제 PLC 제어 환경과 유사한 반응성 제공.
- **심미성**: 표준적인 브라우저 컨트롤을 넘어선 현대적인 디자인 시스템 적용으로 고품질의 도구 느낌 구현.

### ⚠️ 개선 가능성
- **프로토콜 지원**: 현재 3E 프레임(바이너리)만 지원하므로, iQ-R 시리즈 등에서 사용되는 4E 프레임이나 ASCII 방식의 추가 구현이 필요할 수 있음.
- **보안**: Python 스크립트를 `exec()`으로 직접 실행하므로, 신뢰할 수 있는 사용자만 접근 가능한 환경에서 구동하는 것이 권장됨.

## 4. 최종 결과물
- **GitHub Repository**: [Wany-ww/plc_simulator](https://github.com/Wany-ww/plc_simulator)
- **주요 파일**: `main.py`, `simulator/`, `static/`, `README.md`, `IMPLEMENTATION_PLAN.md`.

---
*2026-05-09 Antigravity AI에 의해 생성됨*
