/**
 * 연차 신청서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[annual_leave_scripts_v2.js] Script loaded - Refactored version');

    // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
    if (typeof BaseFormProcessor === 'undefined' || typeof getFormConfig === 'undefined') {
        console.error('[annual_leave_scripts_v2.js] Dependencies not loaded. Waiting...');
        setTimeout(() => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                initAnnualLeaveProcessor();
            } else {
                console.error('[annual_leave_scripts_v2.js] Dependencies still not available');
            }
        }, 100);
        return;
    }

    initAnnualLeaveProcessor();

    function initAnnualLeaveProcessor() {
        /**
         * 연차 신청서 전용 프로세서 클래스
         */
        class AnnualLeaveProcessor extends BaseFormProcessor {
            constructor() {
                const config = getFormConfig('annual_leave');
                if (!config) {
                    console.error('[AnnualLeaveProcessor] Configuration not found');
                    return;
                }
                
                super(config);
            }

            /**
             * 추가 초기화 - 연차 특화 기능
             */
            onAfterInit() {
                this.setupLeaveSpecificFeatures();
            }

            /**
             * 연차 특화 기능
             */
            setupLeaveSpecificFeatures() {
                // 연차 신청서 특화 로직
                this.setupLeaveTypeChange();
                this.setupDateValidation();
                console.log('[AnnualLeaveProcessor] Leave-specific features initialized');
            }

            /**
             * 연차 종류 변경 시 처리
             */
            setupLeaveTypeChange() {
                const leaveTypeSelect = this.form.querySelector('#leave_type');
                if (leaveTypeSelect) {
                    leaveTypeSelect.addEventListener('change', (e) => {
                        const selectedType = e.target.value;
                        console.log(`[AnnualLeaveProcessor] Leave type changed to: ${selectedType}`);
                        
                        // 반차/반반차 선택 시 종료일 자동 설정
                        if (selectedType === '반차' || selectedType === '반반차') {
                            this.handleHalfDayLeave();
                        }
                    });
                }
            }

            /**
             * 반차/반반차 처리
             */
            handleHalfDayLeave() {
                const startDateInput = this.form.querySelector('#leave_start_date');
                const endDateInput = this.form.querySelector('#leave_end_date');
                
                if (startDateInput && endDateInput && startDateInput.value) {
                    // 반차/반반차는 시작일과 종료일이 같음
                    endDateInput.value = startDateInput.value;
                    console.log('[AnnualLeaveProcessor] Half-day leave dates synchronized');
                }
            }

            /**
             * 날짜 유효성 검사
             */
            setupDateValidation() {
                const startDateInput = this.form.querySelector('#leave_start_date');
                const endDateInput = this.form.querySelector('#leave_end_date');
                
                if (startDateInput && endDateInput) {
                    startDateInput.addEventListener('change', () => {
                        if (startDateInput.value && endDateInput.value) {
                            const startDate = new Date(startDateInput.value);
                            const endDate = new Date(endDateInput.value);
                            
                            if (startDate > endDate) {
                                alert('시작일이 종료일보다 늦을 수 없습니다.');
                                startDateInput.focus();
                            }
                        }
                    });
                    
                    endDateInput.addEventListener('change', () => {
                        if (startDateInput.value && endDateInput.value) {
                            const startDate = new Date(startDateInput.value);
                            const endDate = new Date(endDateInput.value);
                            
                            if (endDate < startDate) {
                                alert('종료일이 시작일보다 빠를 수 없습니다.');
                                endDateInput.focus();
                            }
                        }
                    });
                }
            }
        }

        // 프로세서 인스턴스 생성
        new AnnualLeaveProcessor();
    }

    console.log('[annual_leave_scripts_v2.js] Script completed');
})(); 