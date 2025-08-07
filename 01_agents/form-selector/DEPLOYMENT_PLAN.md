# 신규 디자인(퍼블리싱) 적용 및 통합 계획

이 문서는 `templates/publishing` 폴더에 포함된 새로운 디자인을 기존 프로젝트에 안전하게 통합하기 위한 단계별 계획을 설명합니다.

---

### **1단계: 정적 파일(Assets) 재배치 및 정리**

새로운 디자인에 필요한 `js`, `scss`, `plugins` 파일을 `static` 폴더로 옮기고, 기존 파일과의 충돌을 방지하기 위해 사용하지 않는 파일들을 정리합니다.

1.  **새로운 정적 파일 복사:**
    *   `C:\...\static\publish\js\` 폴더의 모든 `.js` 파일을 프로젝트의 `static/js/` 폴더로 복사합니다.
    *   `C:\...\static\publish\plugins` 폴더를 통째로 `static/` 폴더 아래로 복사하여 `static/plugins/` 구조를 만듭니다.
    *   `C:\...\static\publish\scss` 폴더를 통째로 `static/` 폴더 아래로 복사하여 `static/scss/` 구조를 만듭니다.

2.  **기존 정적 파일 정리:**
    *   기존에 사용하던 `static/style.css` 파일을 백업 후 삭제하여 새로운 스타일시트와 충돌하지 않도록 합니다.
    *   `static/js/` 폴더에서 더 이상 사용되지 않는 이전 스크립트 파일들을 확인하고 백업 후 삭제합니다. (예: `annual_leave_scripts.js` 등 구버전 파일)

### **2단계: SCSS 컴파일 설정**

브라우저가 읽을 수 있도록 `SCSS` 파일을 `CSS`로 변환합니다.

1.  **Sass 컴파일러 설치 (필요시):**
    *   시스템에 Sass가 설치되어 있지 않다면 터미널을 통해 설치합니다.
    ```bash
    npm install -g sass
    ```

2.  **CSS 폴더 생성:**
    *   컴파일된 CSS 파일을 저장할 `static/css` 폴더를 생성합니다. (이미 존재하면 생략)

3.  **SCSS 컴파일 실행:**
    *   터미널에서 다음 명령어를 실행하여 `static/scss/` 폴더의 메인 SCSS 파일을 `static/css/style.css`로 컴파일합니다.
    ```bash
    sass static/scss/style.scss static/css/style.css --no-source-map
    ```
    *   `--no-source-map` 옵션을 추가하여 불필요한 맵 파일을 생성하지 않습니다.

### **3단계: 템플릿 경로 수정 및 적용**

FastAPI가 새로운 템플릿을 렌더링하고, 템플릿 파일들이 올바른 정적 파일을 참조하도록 경로를 수정합니다.

1.  **FastAPI 템플릿 경로 변경 (`main.py`):**
    *   `main.py`에서 `Jinja2Templates`의 `directory`를 `'templates/publishing'`으로 변경하여 애플리케이션이 새로운 디자인의 HTML 파일을 렌더링하도록 설정합니다.
    ```python
    # 수정 전
    # templates = Jinja2Templates(directory="templates")

    # 수정 후
    templates = Jinja2Templates(directory="templates/publishing")
    ```

2.  **HTML 파일 내 정적 파일 경로 업데이트:**
    *   `templates/publishing/` 폴더의 모든 HTML 파일을 열어 CSS 및 JS 파일 경로를 FastAPI의 `url_for`를 사용하도록 수정합니다. 이렇게 하면 정적 파일 경로가 변경되어도 유연하게 대처할 수 있습니다.
    *   **CSS 경로 수정 예시:**
        ```html
        <!-- <link rel="stylesheet" href="../static/css/style.css"> --> <!-- 기존 방식 -->
        <link rel="stylesheet" href="{{ url_for('static', path='css/style.css') }}"> <!-- 수정 후 -->
        ```
    *   **JavaScript 경로 수정 예시:**
        ```html
        <!-- <script src="../static/js/script.js"></script> --> <!-- 기존 방식 -->
        <script src="{{ url_for('static', path='js/script.js') }}"></script> <!-- 수정 후 -->
        <script src="{{ url_for('static', path='plugins/datepicker/datepicker.js') }}"></script> <!-- 플러그인 예시 -->
        ```

### **4단계: 시스템 검증**

모든 변경 사항이 올바르게 적용되었는지 확인합니다.

1.  **애플리케이션 실행:**
    *   FastAPI 서버를 실행합니다.

2.  **기능 및 UI 테스트:**
    *   웹 브라우저에서 각 서식 페이지에 접속하여 다음을 확인합니다.
        *   **UI 확인:** 새로운 디자인(폰트, 색상, 레이아웃 등)이 깨짐 없이 정상적으로 표시되는지 확인합니다.
        *   **기능 확인:** 날짜 선택(Datepicker), 동적 테이블(항목 추가/삭제), 스피너 등 모든 JavaScript 기반 기능들이 올바르게 동작하는지 테스트합니다.
        *   **콘솔 오류 확인:** 브라우저의 개발자 도구(F12) 콘솔 탭에서 파일 로드 실패(404)나 스크립트 오류가 없는지 확인합니다.

---

이 계획에 따라 진행하면 새로운 디자인을 체계적으로 프로젝트에 통합할 수 있습니다. 각 단계별로 실행하시면서 궁금한 점이 생기면 언제든지 질문해주세요.