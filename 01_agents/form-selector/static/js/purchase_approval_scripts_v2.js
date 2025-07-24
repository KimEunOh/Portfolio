/**
 * 구매 품의서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[purchase_approval_scripts_v2.js] Script loaded - Refactored version');

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
             * 데이터 로딩 로직을 오버라이드하여 동적 테이블 생성을 먼저 수행.
             * 이것이 자동 생성 문제 해결의 핵심입니다.
             */
            loadInitialData() {
                console.log(`[PurchaseApprovalProcessor] Overridden loadInitialData CALLED.`);

                if (!this.itemsDataScript || !this.itemsDataScript.textContent || this.itemsDataScript.textContent.trim() === '{items_json}') {
                    console.log(`[PurchaseApprovalProcessor] No initial data found. Calling super.loadInitialData to handle default behavior.`);
                    super.loadInitialData();
                    return;
                }

                try {
                    const parsedData = JSON.parse(this.itemsDataScript.textContent);
                    const items = this.extractItemsFromData(parsedData);
                    console.log(`[PurchaseApprovalProcessor] Found ${items.length} items to process.`);

                    if (items.length > 1) {
                        const table = this.form.querySelector('#purchase_table');
                        const templateItem = table ? table.querySelector('tbody') : null;

                        if (templateItem) {
                            console.log(`[PurchaseApprovalProcessor] Template <tbody> found. Starting dynamic creation...`);
                            // 기존 복제본 삭제
                            const allItems = table.querySelectorAll('tbody');
                            for (let i = 1; i < allItems.length; i++) allItems[i].remove();

                            // 두 번째 아이템부터 템플릿 복제
                            for (let i = 1; i < items.length; i++) {
                                const newItem = templateItem.cloneNode(true);
                                const newItemIndex = i + 1;
                                console.log(`[PurchaseApprovalProcessor] Creating tbody for item ${newItemIndex}...`);

                                newItem.querySelectorAll('input, select, textarea').forEach(input => {
                                    const id = input.id || '';
                                    if (id) input.id = id.replace(/_1$/, `_${newItemIndex}`);
                                    if (input.name) input.name = input.name.replace(/_1$/, `_${newItemIndex}`);
                                    input.value = ''; // 값 초기화
                                });
                                table.appendChild(newItem);
                            }
                            console.log(`[PurchaseApprovalProcessor] Finished dynamic creation. Table now has ${table.querySelectorAll('tbody').length} tbodys.`);
                        }
                    }
                } catch (e) {
                    console.error(`[PurchaseApprovalProcessor] Error during pre-processing in loadInitialData:`, e);
                }

                console.log(`[PurchaseApprovalProcessor] All structures ready. Calling super.loadInitialData() to populate fields.`);
                super.loadInitialData();
            }

            /**
             * 추가 초기화 - 구매 품의서 특화 기능
             */
            onAfterInit() {
                this.setupDraftDate();
                this.setupPurchaseSpecificFeatures();
            }

            /**
             * 기안일 자동 설정
             */
            setupDraftDate() {
                const draftDateInput = this.form.querySelector('#draft_date');
                if (draftDateInput && !draftDateInput.value) {
                    draftDateInput.value = new Date().toISOString().split('T')[0];
                }
            }

            /**
             * 구매 품의서 특화 기능 (버튼 이벤트 직접 처리)
             */
            setupPurchaseSpecificFeatures() {
                const init = () => {
                    if (window.initializeDynamicTable) {
                        window.initializeDynamicTable('purchase_table', 'add_row_btn', 'remove_row_btn');
                    }
                };

                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', init);
                } else {
                    init();
                }
            }
        }

        // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
        const checkDependencies = () => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                new PurchaseApprovalProcessor();
            } else {
                setTimeout(checkDependencies, 100);
            }
        };
        checkDependencies();
    }

    initPurchaseApprovalProcessor();

    console.log('[purchase_approval_scripts_v2.js] Script completed');
})(); 