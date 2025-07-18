/**
 * 개인 경비 사용내역서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[personal_expense_scripts.js] Script loaded - Refactored version');

    // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
    if (typeof BaseFormProcessor === 'undefined' || typeof getFormConfig === 'undefined') {
        console.error('[personal_expense_scripts.js] Dependencies not loaded. Waiting...');
        // 간단한 재시도 로직
        setTimeout(() => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                initPersonalExpenseProcessor();
            } else {
                console.error('[personal_expense_scripts.js] Dependencies still not available');
            }
        }, 100);
        return;
    }

    initPersonalExpenseProcessor();

    function initPersonalExpenseProcessor() {
        /**
         * 개인 경비 전용 프로세서 클래스
         */
        class PersonalExpenseProcessor extends BaseFormProcessor {
            constructor() {
                const config = getFormConfig('personal_expense');
                if (!config) {
                    console.error('[PersonalExpenseProcessor] Configuration not found');
                    return;
                }
                
                super(config);
            }

            /**
             * 추가 초기화 - 기안일 자동 설정
             */
            onAfterInit() {
                this.setupDraftDate();
                this.setupDynamicItemAddition();
            }

            /**
             * 기안일 자동 설정
             */
            setupDraftDate() {
                const draftDateInput = this.form.querySelector('#draft_date');
                if (draftDateInput && !draftDateInput.value) {
                    draftDateInput.value = new Date().toISOString().split('T')[0];
                    console.log('[PersonalExpenseProcessor] Draft date set to today');
                }
            }

            /**
             * 동적 항목 추가 기능 (기존 IIFE 코드 통합)
             */
            setupDynamicItemAddition() {
                const container = this.form.querySelector('#personal-expense-items-container');
                const addButton = this.form.querySelector('#add-personal-expense-item');
                
                if (!container || !addButton) {
                    console.warn('[PersonalExpenseProcessor] Dynamic item addition elements not found');
                    return;
                }

                let expenseItemCounter = container.querySelectorAll('.item-set').length;

                addButton.addEventListener('click', () => {
                    expenseItemCounter++;
                    const newItemHtml = `
                        <div class="item-set">
                            <h4>경비 항목 ${expenseItemCounter}</h4>
                            <div class="item-fields-grid">
                                <div class="form-group"><label for="expense_date_${expenseItemCounter}">사용일자:</label><input type="date" id="expense_date_${expenseItemCounter}" name="expense_date_${expenseItemCounter}" class="form-control"></div>
                                <div class="form-group"><label for="expense_category_${expenseItemCounter}">분류:</label><select id="expense_category_${expenseItemCounter}" name="expense_category_${expenseItemCounter}" class="form-control"><option value="">선택</option><option value="traffic">교통비</option><option value="accommodation">숙박비</option><option value="meals">식대</option><option value="entertainment">접대비</option><option value="education">교육훈련비</option><option value="supplies">소모품비</option><option value="other">기타</option></select></div>
                                <div class="form-group"><label for="expense_description_${expenseItemCounter}">사용내역:</label><input type="text" id="expense_description_${expenseItemCounter}" name="expense_description_${expenseItemCounter}" class="form-control"></div>
                                <div class="form-group"><label for="expense_amount_${expenseItemCounter}">금액:</label><input type="number" id="expense_amount_${expenseItemCounter}" name="expense_amount_${expenseItemCounter}" class="form-control expense-amount-calc"></div>
                                <div class="form-group"><label for="expense_notes_${expenseItemCounter}">비고:</label><input type="text" id="expense_notes_${expenseItemCounter}" name="expense_notes_${expenseItemCounter}" class="form-control"></div>
                            </div>
                        </div>`;
                    container.insertAdjacentHTML('beforeend', newItemHtml);
                    console.log(`[PersonalExpenseProcessor] Item ${expenseItemCounter} added`);
                });

                // 컨테이너에 이벤트 위임으로 동적 항목 처리
                container.addEventListener('input', (e) => {
                    if (e.target.classList.contains('expense-amount-calc')) {
                        this.calculateOverallTotal();
                    }
                });
            }
        }

        // 프로세서 인스턴스 생성
        new PersonalExpenseProcessor();
    }

    console.log('[personal_expense_scripts.js] Script completed');
})();
