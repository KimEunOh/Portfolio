/**
 * 교통비 신청서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[transportation_expense_scripts_v2.js] Script loaded - Refactored version');

    // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
    if (typeof BaseFormProcessor === 'undefined' || typeof getFormConfig === 'undefined') {
        console.error('[transportation_expense_scripts_v2.js] Dependencies not loaded. Waiting...');
        setTimeout(() => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                initTransportationExpenseProcessor();
            } else {
                console.error('[transportation_expense_scripts_v2.js] Dependencies still not available');
            }
        }, 100);
        return;
    }

    initTransportationExpenseProcessor();

    function initTransportationExpenseProcessor() {
        /**
         * 교통비 전용 프로세서 클래스
         */
        class TransportationExpenseProcessor extends BaseFormProcessor {
            constructor() {
                const config = getFormConfig('transportation_expense');
                if (!config) {
                    console.error('[TransportationExpenseProcessor] Configuration not found');
                    return;
                }
                
                super(config);
            }

            /**
             * 추가 초기화 - 교통비 특화 기능
             */
            onAfterInit() {
                this.setupTransportationSpecificFeatures();
            }

            /**
             * 교통비 특화 기능
             */
            setupTransportationSpecificFeatures() {
                // 교통비 특화 로직
                this.setupLocationValidation();
                this.setupAmountValidation();
                this.setupTransportDateDefault();
                console.log('[TransportationExpenseProcessor] Transportation-specific features initialized');
            }

            /**
             * 교통일 기본값 설정
             */
            setupTransportDateDefault() {
                const transportDateInput = this.form.querySelector('#transport_date');
                if (transportDateInput && !transportDateInput.value) {
                    transportDateInput.value = new Date().toISOString().split('T')[0];
                    console.log('[TransportationExpenseProcessor] Transport date set to today');
                }
            }

            /**
             * 출발지/도착지 유효성 검사
             */
            setupLocationValidation() {
                const departureInput = this.form.querySelector('#departure_location');
                const arrivalInput = this.form.querySelector('#arrival_location');
                
                if (departureInput && arrivalInput) {
                    const validateLocations = () => {
                        if (departureInput.value && arrivalInput.value) {
                            if (departureInput.value.trim() === arrivalInput.value.trim()) {
                                alert('출발지와 도착지가 같을 수 없습니다.');
                                arrivalInput.focus();
                                return false;
                            }
                            
                            console.log(`[TransportationExpenseProcessor] Route: ${departureInput.value} → ${arrivalInput.value}`);
                            return true;
                        }
                        return false;
                    };
                    
                    departureInput.addEventListener('blur', validateLocations);
                    arrivalInput.addEventListener('blur', validateLocations);
                }
            }

            /**
             * 교통비 금액 유효성 검사
             */
            setupAmountValidation() {
                const amountInput = this.form.querySelector('#transport_amount');
                
                if (amountInput) {
                    amountInput.addEventListener('input', (e) => {
                        const value = e.target.value;
                        
                        // 숫자가 아닌 문자 제거
                        const numericValue = value.replace(/[^0-9]/g, '');
                        if (numericValue !== value) {
                            e.target.value = numericValue;
                        }
                        
                        // 금액 유효성 검사
                        const amount = parseInt(numericValue);
                        if (amount > 1000000) {
                            alert('교통비는 100만원을 초과할 수 없습니다.');
                            e.target.focus();
                        }
                        
                        console.log(`[TransportationExpenseProcessor] Amount updated: ${amount}`);
                    });
                    
                    amountInput.addEventListener('blur', (e) => {
                        const amount = parseInt(e.target.value);
                        if (amount > 0 && amount < 1000) {
                            const confirmResult = confirm('교통비가 1,000원 미만입니다. 계속하시겠습니까?');
                            if (!confirmResult) {
                                e.target.focus();
                            }
                        }
                    });
                }
            }
        }

        // 프로세서 인스턴스 생성
        new TransportationExpenseProcessor();
    }

    console.log('[transportation_expense_scripts_v2.js] Script completed');
})(); 