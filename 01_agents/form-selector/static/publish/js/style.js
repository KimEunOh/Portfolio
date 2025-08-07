$(document).ready(function(){
    //select
    niceSelect();

    // input
    inputActive();
});
function niceSelect(target = 'body') {
    let $container = $(target);

    // 기존 select 요소에 niceSelect 적용
    $container.find('select').not('.nice-initialized').each(function () {
        $(this).addClass('nice-initialized').niceSelect();
    });

    $container.find('.nice-select').each(function () {
        let niceSelect = $(this),
            select = niceSelect.prev('select');

        // placeholder 설정
        if (niceSelect.find('ul.list li:first-child').hasClass('selected disabled')) {
            niceSelect.addClass('placeholder');
        } else {
            niceSelect.removeClass('placeholder');
        }

        select.on('change', function () {
            niceSelect.removeClass('placeholder');
        });
    });
}

// niceSelect 드롭다운
function selDropDown(niceSelect) {
    const offsetSel = niceSelect[0].getBoundingClientRect();

    // 드롭다운 ul 위치 조정 (스크롤 내릴 때 기준 컨테이너를 넘어가지 않도록)
    niceSelect.find('ul.list').css({
        top: Math.floor(offsetSel.top + offsetSel.height - 1),
        left: Math.round(offsetSel.left)
    });
}

// 데이터피커
function fn_setDatePicker(selector, option) {
    if (!option) {
        option = {};
    }
    let isClosing = false;

    $.datetimepicker.setLocale('ko');
    let _option = {
        timepicker: false,
        format: 'Y.m.d',
        scrollMonth: false,
        scrollInput: false,
        lang: 'ko',
        i18n: {
            ko: {
                dayOfWeek: [
                    "일", "월", "화", "수", "목", "금", "토"
                ]
            }
        },
        onClose: function(dp, $input) {
            if (!isClosing) {
                isClosing = true;
                setTimeout(() => {
                    $input.blur();
                    isClosing = false;
                }, 0);
            }
        },
        ...option
    }
    $(selector).datetimepicker(_option);

    $(selector).on('change', function() {
        const termForm = $(this).closest('.term_form');
        termForm.find('.btn').removeClass('active');
        $(this).closest('.input').toggleClass('active', $(this).val().trim() !== '');
    });
}

function fn_setTimePicker(selector, option) {
    if (!option) {
        option = {};
    }
    const userOnShow = option.onShow;
    let isClosing = false;
    let _option = {
        ...option,
        datepicker: false,
        format: 'H:i',
        onShow: function (ct, $input, inst) {
            timepickerScroll();

            // 사용자 정의 onShow 호출
            if (typeof userOnShow === 'function') {
                userOnShow.call(this, ct, $input, inst);
            }
        },
        onClose: function(ct, $input) {
            if (!isClosing) {
                isClosing = true;
                setTimeout(() => {
                    $input.blur();
                    isClosing = false;
                }, 0);
            }
        },
    }
    $(selector).datetimepicker(_option);

    $(selector).on('change', function() {
        $(this).closest('.input').toggleClass('active', $(this).val().trim() !== '');
    });
}
function timepickerScroll() {
    setTimeout(function () {
        let $picker = $('.xdsoft_datetimepicker:visible'); // 열린 캘린더
        let $timepicker = $picker.find('.xdsoft_timepicker .xdsoft_time_box');
        let $timeVariant = $timepicker.find('.xdsoft_time_variant');

        $timepicker.off('DOMMouseScroll mousewheel').on('DOMMouseScroll mousewheel', function (e) {
            // 라이브러리에서 제공하는 휠 이벤트 차단
            e.stopPropagation();
        });

        let $selectedTime = $timeVariant.find('.xdsoft_current');
        if ($selectedTime.length) {
            // 선택된 시간 위치에 맞게 스크롤 이동
            let timeOffset = $selectedTime.offset().top - $timeVariant.offset().top;
            $timepicker.scrollTop(timeOffset);
        }
    }, 10);
}
// input
function inputActive(target = 'body') {
    let $container = $(target);

    const toggleActiveState = (element) => {
        const container = element.closest('.input, .search');
        container.toggleClass('active', element.val().trim() !== '');
    };

    const resetValidationState = (container) => {
        container.removeClass('success error');
    };

    // 최초 실행 시 이벤트 바인딩 (중복 실행 방지)
    if (!window._inputActiveInitialized) {
        window._inputActiveInitialized = true;

        $(document).on({
            input: function () {
                toggleActiveState($(this));
            },
            focusin: function () {
                toggleActiveState($(this));
            },
            keyup: function () {
                resetValidationState($(this).closest('.input, .search'));
            }
        }, '.input input, .search input');

        $(document).on('mousedown', '.btn_del', function () {
            const container = $(this).closest('.input, .search');
            container.removeClass('active').find('input').val('');

            if (container.closest('.term_form').length) {
                container.closest('.term_form').find('.btn').removeClass('active');
            }
        });

        $(document).on('keyup', 'input.only_kor', function () {
            const pattern = /[a-z0-9]|[ \[\]{}()<>?|`~!@#$%^&*-_+=,.;:\"'\\]/g;
            this.value = this.value.replace(pattern, '');
        });

        $(document).on('keyup', 'input.only_eng', function () {
            const pattern = /[^A-Za-z\s]/ig;
            this.value = this.value.replace(pattern, '');
        });
    }

    // 특정 컨테이너 내 요소만 업데이트
    $container.find('.input input, .search input').each(function () {
        toggleActiveState($(this));
    });

    // 숫자 콤마 포맷 적용 (중복 방지)
    $container.find('.comma').not('.comma-initialized').each(function () {
        $(this).addClass('comma-initialized').inputmask('numeric', {
            autoGroup: true,
            groupSeparator: ',',
        });
    }).on('keyup', function () {
        if ($(this).val().includes('-')) {
            $(this).val('');
        }
    });

    // 전화번호 - 포맷 적용 (중복 방지)
    $container.find('.tel').not('.tel-initialized').each(function () {
        $(this).addClass('tel-initialized').inputmask('999-9999-9999', {
            showMaskOnHover: false,
            showMaskOnFocus: false,
        });
    });

    // 전화번호 - 포맷 적용 (중복 방지)
    $container.find('.mask').not('mask-initialized').each(function () {
        $(this).addClass('mask-initialized').inputmask('9999 9999 9999 9999', {
            showMaskOnHover: false,
            showMaskOnFocus: false,
            oncomplete: function () {
                const raw = $(this).inputmask('unmaskedvalue');
                if (raw.length === 16) {
                    const masked = `${raw.slice(0, 4)} ${raw.slice(4, 8)} **** ${raw.slice(12, 16)}`;
                    $(this).val(masked);
                }
            }
        });
    });
}
