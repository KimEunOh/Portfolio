/**
 * 법인카드 지출내역서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[corporate_card_scripts_v2.js] Script loaded - Refactored version');

    // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
    if (typeof BaseFormProcessor === 'undefined' || typeof getFormConfig === 'undefined') {
        console.error('[corporate_card_scripts_v2.js] Dependencies not loaded. Waiting...');
        setTimeout(() => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                initCorporateCardProcessor();
            } else {
                console.error('[corporate_card_scripts_v2.js] Dependencies still not available');
            }
        }, 100);
        return;
    }

    initCorporateCardProcessor();

    function initCorporateCardProcessor() {
        /**
         * 법인카드 전용 프로세서 클래스
         */
        class CorporateCardProcessor extends BaseFormProcessor {
            constructor() {
                const config = getFormConfig('corporate_card');
                if (!config) {
                    console.error('[CorporateCardProcessor] Configuration not found');
                    return;
                }
                
                super(config);
            }

            /**
             * 추가 초기화 - 법인카드 특화 기능
             */
            onAfterInit() {
                this.setupCardSpecificFeatures();
            }

            /**
             * 법인카드 특화 기능
             */
            setupCardSpecificFeatures() {
                // 법인카드 특화 로직이 필요한 경우 여기에 추가
                console.log('[CorporateCardProcessor] Card-specific features initialized');
            }
        }

        // 프로세서 인스턴스 생성
        new CorporateCardProcessor();
    }

    console.log('[corporate_card_scripts_v2.js] Script completed');
})(); 