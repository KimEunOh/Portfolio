/**
 * 야근 식대 신청서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[dinner_expense_scripts_v2.js] Script loaded - Refactored version');

    // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
    if (typeof BaseFormProcessor === 'undefined' || typeof getFormConfig === 'undefined') {
        console.error('[dinner_expense_scripts_v2.js] Dependencies not loaded. Waiting...');
        setTimeout(() => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                initDinnerExpenseProcessor();
            } else {
                console.error('[dinner_expense_scripts_v2.js] Dependencies still not available');
            }
        }, 100);
        return;
    }

    initDinnerExpenseProcessor();

    function initDinnerExpenseProcessor() {
        /**
         * 야근 식대 전용 프로세서 클래스
         */
        class DinnerExpenseProcessor extends BaseFormProcessor {
            constructor() {
                const config = getFormConfig('dinner_expense');
                if (!config) {
                    console.error('[DinnerExpenseProcessor] Configuration not found');
                    return;
                }
                
                super(config);
            }

            /**
             * 추가 초기화 - 야근 식대 특화 기능
             */
            onAfterInit() {
                this.setupDinnerSpecificFeatures();
            }

            /**
             * 야근 식대 특화 기능
             */
            setupDinnerSpecificFeatures() {
                // 야근 식대 특화 로직
                this.setupTimeValidation();
                this.setupWorkDateDefault();
                this.setupMealAmountCalculation();
                console.log('[DinnerExpenseProcessor] Dinner expense-specific features initialized');
            }

            /**
             * 근무일 기본값 설정
             */
            setupWorkDateDefault() {
                const workDateInput = this.form.querySelector('#work_date');
                if (workDateInput && !workDateInput.value) {
                    workDateInput.value = new Date().toISOString().split('T')[0];
                    console.log('[DinnerExpenseProcessor] Work date set to today');
                }
            }

            /**
             * 시간 유효성 검사
             */
            setupTimeValidation() {
                const startTimeInput = this.form.querySelector('#work_start_time');
                const endTimeInput = this.form.querySelector('#work_end_time');
                
                if (startTimeInput && endTimeInput) {
                    const validateTimes = () => {
                        if (startTimeInput.value && endTimeInput.value) {
                            const startTime = this.parseTime(startTimeInput.value);
                            const endTime = this.parseTime(endTimeInput.value);
                            
                            if (startTime >= endTime) {
                                alert('시작 시간이 종료 시간보다 늦을 수 없습니다.');
                                startTimeInput.focus();
                                return false;
                            }
                            
                            // 야근 시간 계산 (6시간 이상)
                            const workHours = (endTime - startTime) / (1000 * 60 * 60);
                            if (workHours < 6) {
                                alert('야근 식대는 6시간 이상 근무시에만 신청 가능합니다.');
                                return false;
                            }
                            
                            console.log(`[DinnerExpenseProcessor] Work hours: ${workHours.toFixed(1)}h`);
                            return true;
                        }
                        return false;
                    };
                    
                    startTimeInput.addEventListener('change', validateTimes);
                    endTimeInput.addEventListener('change', validateTimes);
                }
            }

            /**
             * 시간 문자열을 Date 객체로 변환
             */
            parseTime(timeString) {
                if (!timeString) return null;
                
                const [hours, minutes] = timeString.split(':');
                const date = new Date();
                date.setHours(parseInt(hours), parseInt(minutes), 0, 0);
                return date;
            }

            /**
             * 식대 금액 자동 계산
             */
            setupMealAmountCalculation() {
                const mealAmountInput = this.form.querySelector('#meal_amount');
                
                if (mealAmountInput && !mealAmountInput.value) {
                    // 기본 식대 금액 설정 (예: 10,000원)
                    mealAmountInput.value = '10000';
                    console.log('[DinnerExpenseProcessor] Default meal amount set');
                }
            }
        }

        // 프로세서 인스턴스 생성
        new DinnerExpenseProcessor();
    }

    console.log('[dinner_expense_scripts_v2.js] Script completed');
})(); 