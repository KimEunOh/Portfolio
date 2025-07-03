/**
 * 파견 및 출장 보고서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[dispatch_report_scripts_v2.js] Script loaded - Refactored version');

    // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
    if (typeof BaseFormProcessor === 'undefined' || typeof getFormConfig === 'undefined') {
        console.error('[dispatch_report_scripts_v2.js] Dependencies not loaded. Waiting...');
        setTimeout(() => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                initDispatchReportProcessor();
            } else {
                console.error('[dispatch_report_scripts_v2.js] Dependencies still not available');
            }
        }, 100);
        return;
    }

    initDispatchReportProcessor();

    function initDispatchReportProcessor() {
        /**
         * 파견/출장 보고서 전용 프로세서 클래스
         */
        class DispatchReportProcessor extends BaseFormProcessor {
            constructor() {
                const config = getFormConfig('dispatch_report');
                if (!config) {
                    console.error('[DispatchReportProcessor] Configuration not found');
                    return;
                }
                
                super(config);
            }

            /**
             * 추가 초기화 - 파견/출장 특화 기능
             */
            onAfterInit() {
                this.setupDispatchSpecificFeatures();
            }

            /**
             * 파견/출장 특화 기능
             */
            setupDispatchSpecificFeatures() {
                // 파견/출장 특화 로직
                this.setupDateValidation();
                this.setupDurationCalculation();
                this.setupReportValidation();
                console.log('[DispatchReportProcessor] Dispatch report-specific features initialized');
            }

            /**
             * 날짜 유효성 검사
             */
            setupDateValidation() {
                const startDateInput = this.form.querySelector('#dispatch_start_date');
                const endDateInput = this.form.querySelector('#dispatch_end_date');
                
                if (startDateInput && endDateInput) {
                    const validateDates = () => {
                        if (startDateInput.value && endDateInput.value) {
                            const startDate = new Date(startDateInput.value);
                            const endDate = new Date(endDateInput.value);
                            
                            if (startDate > endDate) {
                                alert('시작일이 종료일보다 늦을 수 없습니다.');
                                startDateInput.focus();
                                return false;
                            }
                            
                            // 기간 자동 계산
                            this.calculateDuration(startDate, endDate);
                            return true;
                        }
                        return false;
                    };
                    
                    startDateInput.addEventListener('change', validateDates);
                    endDateInput.addEventListener('change', validateDates);
                }
            }

            /**
             * 파견/출장 기간 자동 계산
             */
            calculateDuration(startDate, endDate) {
                const durationInput = this.form.querySelector('#dispatch_duration_days');
                
                if (durationInput) {
                    const timeDiff = endDate.getTime() - startDate.getTime();
                    const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24)) + 1; // 당일 포함
                    
                    durationInput.value = daysDiff;
                    console.log(`[DispatchReportProcessor] Duration calculated: ${daysDiff} days`);
                }
            }

            /**
             * 기간 계산 설정
             */
            setupDurationCalculation() {
                const durationInput = this.form.querySelector('#dispatch_duration_days');
                
                if (durationInput) {
                    durationInput.addEventListener('input', (e) => {
                        const value = parseInt(e.target.value);
                        
                        if (value > 365) {
                            alert('파견/출장 기간은 1년(365일)을 초과할 수 없습니다.');
                            e.target.focus();
                        } else if (value < 1) {
                            alert('파견/출장 기간은 최소 1일 이상이어야 합니다.');
                            e.target.focus();
                        }
                        
                        console.log(`[DispatchReportProcessor] Duration updated: ${value} days`);
                    });
                }
            }

            /**
             * 보고서 내용 유효성 검사
             */
            setupReportValidation() {
                const purposeInput = this.form.querySelector('#dispatch_purpose');
                const reportDetailsInput = this.form.querySelector('#report_details');
                
                if (purposeInput) {
                    purposeInput.addEventListener('blur', (e) => {
                        if (e.target.value.trim().length < 10) {
                            alert('파견/출장 목적은 10자 이상 작성해주세요.');
                            e.target.focus();
                        }
                    });
                }
                
                if (reportDetailsInput) {
                    reportDetailsInput.addEventListener('blur', (e) => {
                        if (e.target.value.trim().length < 50) {
                            alert('보고서 내용은 50자 이상 작성해주세요.');
                            e.target.focus();
                        }
                    });
                }
            }
        }

        // 프로세서 인스턴스 생성
        new DispatchReportProcessor();
    }

    console.log('[dispatch_report_scripts_v2.js] Script completed');
})(); 