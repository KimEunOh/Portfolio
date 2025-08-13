(function(){
  /*
   * 파견 및 출장 보고서 어댑터
   * - 역할: 슬롯 값 자동 채움(기간/출발지/목적/보고/비고) → 결재라인 렌더/조회
   * - 서버 연계: `form_selector/processors/dispatch_report_processor.py` 및 Legacy 변환과 호환
   * - 중요: 기간 입력(`searchStDt`, `searchEdDt`)과 id/name 매핑에 의존
   */
  // 파견/출장 보고서: 단일 필드 위주 + 기간 표시 보조
  var aliasMap = {
    start_date: ['startDate','searchStDt'],
    end_date: ['endDate','searchEdDt'],
    origin: ['origin'],
    destination: ['destination'],
    purpose: ['purpose'],
    report_details: ['reportDetails'],
    notes: ['notes']
  };
  var normalizers = {};

  // URL 경로에서 mstPid 추출 (결재라인 조회 시 사용)
  function getPidFromPath(){ try{ var m = window.location.pathname.match(/\/master\/(\d+)/); if(m&&m[1]) return Number(m[1]); }catch(e){} return null; }

  // 입력 요소가 비어 있을 때만 값을 채우고 input/change 이벤트를 발생시킴
  function setIfEmpty(selector, value){
    try{
      var el = document.querySelector(selector);
      if(!el) return;
      var cur = (el.value==null? '' : String(el.value).trim());
      var isPlaceholder = /^\{[^}]*\}$/.test(cur) || /SLOT_NOT_FOUND/i.test(cur);
      if(cur==='' || isPlaceholder){
        el.value = value != null ? value : '';
        try{ el.dispatchEvent(new Event('input',{bubbles:true})); }catch(_){ }
        try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(_){ }
      }
    }catch(_){ }
  }

  // 기간 필드와 뱃지(총 일수)를 보강: 프로세서 계산값(duration_days)만 사용
  function ensurePeriodFields(slots){
    if(!slots) return;
    try{ console.log('[DispatchReportAdapter][DEBUG] ensurePeriodFields'); }catch(_){ }
    var sd = slots.start_date || slots.startDate || '';
    var ed = slots.end_date || slots.endDate || '';
    if(sd){ setIfEmpty('input[name="startDate"]', sd); setIfEmpty('#searchStDt', sd); }
    if(ed){ setIfEmpty('input[name="endDate"]', ed); setIfEmpty('#searchEdDt', ed); }

    try{
      var raw = (slots.duration_days != null) ? String(slots.duration_days).trim() : '';
      var days = raw === '' ? 0 : (parseInt(raw, 10) || 0);
      var dtLabel = document.querySelector('dt label[for="searchStDt"]');
      if(dtLabel){
        var dt = dtLabel.closest('dt');
        if(dt){
          var badge = dt.querySelector('.badge');
          if(badge){ badge.textContent = '총 일수 : ' + (days || 0); }
        }
      }
    }catch(_){ }
  }

  // 부트스트랩: 슬롯 채움 → 결재라인 렌더/조회 → UI 리이니셜라이즈
  async function bootstrap(slots, approverInfo){
    try{ console.log('[DispatchReportAdapter][DEBUG] bootstrap start'); }catch(_){ }
    if(window.ExternalSlots && window.ExternalSlots.fillSlots){
      window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers });
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 200);
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 800);
    }

    // 기간/총일수 표시 보강 (서버 계산값 사용)
    try{ ensurePeriodFields(slots||{}); }catch(_){ }

    if(window.ApproverIntegration){
      window.ApproverIntegration.renderApprovalLine(approverInfo||{});
      if(!approverInfo || !approverInfo.approvers || !approverInfo.approvers.length){
        var pid = (slots && (slots.mst_pid || slots.mstPid)) || getPidFromPath();
        var drafterId = (slots && (slots.drafter_id || slots.drafterId)) || null;
        if(pid && window.ApproverIntegration.fetchApproverInfo){
          var info = await window.ApproverIntegration.fetchApproverInfo({ mstPid: pid, drafterId: drafterId });
          if(info){ window.ApproverIntegration.renderApprovalLine(info); }
        }
      }
    }

    try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_){ }
  }

  window.DispatchBusinesstripReportAdapter = { bootstrap: bootstrap };
})();


