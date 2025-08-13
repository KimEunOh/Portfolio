(function(){
  // 야근 식대 폼: 슬롯 → 퍼블리싱 필드 매핑 보강
  var aliasMap = {
    // 표준 snake_case → 퍼블리싱 네이밍
    work_date: ['workDate','date'],
    overtime_time: ['overtimeTime','time'],
    work_location: ['workLocation'],
    dinner_expense_amount: ['dinnerExpenseAmount'],
    bank_account_for_deposit: ['bankAccountForDeposit'],
    work_details: ['workDetails'],
    // 과거 명칭 호환
    dinner_date: ['useYmd','dinnerDate'],
    reason: ['workContent','work_content']
  };

  var normalizers = {
  };

  function getPidFromPath(){
    try{ var m = window.location.pathname.match(/\/master\/(\d+)/); if(m&&m[1]) return Number(m[1]); }catch(e){}
    return null;
  }

  // 입력 요소가 비어 있을 때만 값을 채우고 관련 이벤트를 발생시켜
  // UI 위젯(마스크/포맷터)와 검증 로직이 다시 동작하도록 함
  // - selector: 채울 대상 요소의 CSS 선택자(id/name 등)
  // - value: 채워 넣을 값(없으면 빈 문자열)
  function setIfEmpty(selector, value){
    try{
      var el = document.querySelector(selector);
      if(!el) return;
      if(el.value==null || String(el.value).trim()===''){
        el.value = value != null ? value : '';
        // 값 변경을 알리기 위해 input/change 이벤트를 순서대로 발생
        try{ el.dispatchEvent(new Event('input',{bubbles:true})); }catch(_){ }
        try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(_){ }
      }
    }catch(_){ }
  }

  function ensureDinnerFields(slots){
    try{ console.log('[DinnerAdapter][DEBUG] ensureDinnerFields'); }catch(_){ }
    if(!slots) return;
    // 날짜/시간 필드는 퍼블리싱에서 id가 간단한 경우가 있어 보강
    if(slots.work_date){
      setIfEmpty('input[name="workDate"]', slots.work_date);
      setIfEmpty('#date', slots.work_date);
    }
    if(slots.overtime_time){
      setIfEmpty('input[name="overtimeTime"]', slots.overtime_time);
      setIfEmpty('#time', slots.overtime_time);
    }
    if(slots.work_location){ setIfEmpty('input[name="workLocation"]', slots.work_location); }
    if(slots.dinner_expense_amount!=null){ setIfEmpty('input[name="dinnerExpenseAmount"]', slots.dinner_expense_amount); }
    if(slots.bank_account_for_deposit){ setIfEmpty('input[name="bankAccountForDeposit"]', slots.bank_account_for_deposit); }
    if(slots.work_details){ setIfEmpty('#workDetails', slots.work_details); }
    try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_){ }
  }

  async function bootstrap(slots, approverInfo){
    try{ console.log('[DinnerAdapter][DEBUG] bootstrap start'); }catch(_){ }
    // 1) 슬롯 채우기
    if(window.ExternalSlots && window.ExternalSlots.fillSlots){
      window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers });
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 200);
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 800);
    }
    // 필수 필드 보강 주입
    try{ ensureDinnerFields(slots||{}); }catch(_){ }

    // 2) 결재 라인 렌더링 및 필요 시 조회
    if(window.ApproverIntegration){
      try{ console.log('[DinnerAdapter][DEBUG] renderApprovalLine initial'); }catch(_){ }
      window.ApproverIntegration.renderApprovalLine(approverInfo||{});
      if(!approverInfo || !approverInfo.approvers || !approverInfo.approvers.length){
        var pid = (slots && (slots.mst_pid || slots.mstPid)) || getPidFromPath();
        var drafterId = (slots && (slots.drafter_id || slots.drafterId)) || null;
        if(pid && window.ApproverIntegration.fetchApproverInfo){
          try{ console.log('[DinnerAdapter][DEBUG] fetchApproverInfo pid=', pid, 'drafterId=', drafterId); }catch(_){ }
          var info = await window.ApproverIntegration.fetchApproverInfo({ mstPid: pid, drafterId: drafterId });
          try{ console.log('[DinnerAdapter][DEBUG] fetched approver'); }catch(_){ }
          if(info){ window.ApproverIntegration.renderApprovalLine(info); }
        }
      }
    }
  }

  window.DinnerExpenseAdapter = { bootstrap: bootstrap };
})();

