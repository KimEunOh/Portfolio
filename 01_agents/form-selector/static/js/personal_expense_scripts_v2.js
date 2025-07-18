/**
 * 개인 경비 사용내역서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[personal_expense_scripts_v2.js] Script loaded - Refactored version');

    // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
    if (typeof BaseFormProcessor === 'undefined' || typeof getFormConfig === 'undefined') {
        console.error('[personal_expense_scripts_v2.js] Dependencies not loaded. Waiting...');
        setTimeout(() => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                initPersonalExpenseProcessor();
            } else {
                console.error('[personal_expense_scripts_v2.js] Dependencies still not available');
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
                this.setupExpenseSpecificFeatures();
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
             * 개인경비 특화 기능
             */
            setupExpenseSpecificFeatures() {
                // 개인 경비 특화 로직 (필요시 추가)
                console.log('[PersonalExpenseProcessor] Expense-specific features initialized');
                
                const init = () => {
                    if (window.initializeDynamicTable) {
                        window.initializeDynamicTable('personal_expense_table', 'add_row_btn', 'remove_row_btn');
                    }
                };

                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', init);
                } else {
                    init();
                }
            }
        }

        // 프로세서 인스턴스 생성
        new PersonalExpenseProcessor();
    }

    console.log('[personal_expense_scripts_v2.js] Script completed');
})();
