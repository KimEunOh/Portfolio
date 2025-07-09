/**
 * 구매 품의서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[purchase_approval_scripts_v2.js] Script loaded - Refactored version');

    // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
    if (typeof BaseFormProcessor === 'undefined' || typeof getFormConfig === 'undefined') {
        console.error('[purchase_approval_scripts_v2.js] Dependencies not loaded. Waiting...');
        setTimeout(() => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                initPurchaseApprovalProcessor();
            } else {
                console.error('[purchase_approval_scripts_v2.js] Dependencies still not available');
            }
        }, 100);
        return;
    }

    initPurchaseApprovalProcessor();

    function initPurchaseApprovalProcessor() {
        /**
         * 구매 품의서 전용 프로세서 클래스
         */
        class PurchaseApprovalProcessor extends BaseFormProcessor {
            constructor() {
                const config = getFormConfig('purchase_approval');
                if (!config) {
                    console.error('[PurchaseApprovalProcessor] Configuration not found');
                    return;
                }
                
                super(config);
            }

            /**
             * 추가 초기화 - 구매 품의서 특화 기능
             */
            onAfterInit() {
                this.setupPurchaseSpecificFeatures();
            }

            /**
             * 구매 품의서 특화 기능
             */
            setupPurchaseSpecificFeatures() {
                console.log('[PurchaseApprovalProcessor] Purchase approval-specific features initialized');
                
                const init = () => {
                    if (window.initializeDynamicTable) {
                        window.initializeDynamicTable('purchase_table', 'add_row_btn', 'remove_row_btn');
                    }

                    // draft_date 자동 설정 (오늘 날짜, YYYY-MM-DD)
                    const draftDateInput = document.getElementById('draft_date');
                    if (draftDateInput && !draftDateInput.value) {
                        const today = new Date();
                        const yyyy = today.getFullYear();
                        const mm = String(today.getMonth() + 1).padStart(2, '0');
                        const dd = String(today.getDate()).padStart(2, '0');
                        draftDateInput.value = `${yyyy}-${mm}-${dd}`;
                        console.log('[PurchaseApprovalProcessor] draft_date set to today:', draftDateInput.value);
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
        new PurchaseApprovalProcessor();
    }

    console.log('[purchase_approval_scripts_v2.js] Script completed');
})(); 