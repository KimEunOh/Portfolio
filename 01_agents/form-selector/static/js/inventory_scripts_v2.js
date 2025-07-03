/**
 * 비품/소모품 구입내역서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[inventory_scripts_v2.js] Script loaded - Refactored version');

    // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
    if (typeof BaseFormProcessor === 'undefined' || typeof getFormConfig === 'undefined') {
        console.error('[inventory_scripts_v2.js] Dependencies not loaded. Waiting...');
        setTimeout(() => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                initInventoryProcessor();
            } else {
                console.error('[inventory_scripts_v2.js] Dependencies still not available');
            }
        }, 100);
        return;
    }

    initInventoryProcessor();

    function initInventoryProcessor() {
        /**
         * 비품 전용 프로세서 클래스
         */
        class InventoryProcessor extends BaseFormProcessor {
            constructor() {
                const config = getFormConfig('inventory');
                if (!config) {
                    console.error('[InventoryProcessor] Configuration not found');
                    return;
                }
                
                super(config);
            }

            /**
             * 추가 초기화 - 비품 특화 기능
             */
            onAfterInit() {
                this.setupInventorySpecificFeatures();
            }

            /**
             * 비품 특화 기능
             */
            setupInventorySpecificFeatures() {
                // 비품 관리 특화 로직 (필요시 추가)
                console.log('[InventoryProcessor] Inventory-specific features initialized');
            }
        }

        // 프로세서 인스턴스 생성
        new InventoryProcessor();
    }

    console.log('[inventory_scripts_v2.js] Script completed');
})(); 