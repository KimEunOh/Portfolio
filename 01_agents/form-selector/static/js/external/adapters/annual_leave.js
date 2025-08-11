(function(){
  function normalizeLeaveType(v){
    if(!v) return v;
    var str = String(v).trim().toLowerCase();
    var map = {
      'annual':'annual','연차':'annual','연차휴가':'annual',
      'half_day_morning':'half_day_morning','오전 반차':'half_day_morning','오전반차':'half_day_morning',
      'half_day_afternoon':'half_day_afternoon','오후 반차':'half_day_afternoon','오후반차':'half_day_afternoon',
      'quarter_day_morning':'quarter_day_morning','오전 반반차':'quarter_day_morning','오전반반차':'quarter_day_morning',
      'quarter_day_afternoon':'quarter_day_afternoon','오후 반반차':'quarter_day_afternoon','오후반반차':'quarter_day_afternoon'
    };
    return map[str] || v;
  }

  var aliasMap = {
    start_date: ['startDate','searchStDt'],
    end_date: ['endDate','searchEdDt'],
    leave_type: ['leaveType'],
    leave_days: ['leaveDays'],
    reason: ['reason']
  };

  var normalizers = {
    leave_type: normalizeLeaveType
  };

  function getPidFromPath(){
    try{
      var m = window.location.pathname.match(/\/master\/(\d+)/);
      if(m && m[1]) return Number(m[1]);
    }catch(e){}
    return null;
  }

  async function bootstrapAnnualLeave(slots, approverInfo){
    try{ if(window.__FORM_DEBUG__){ console.log('[AnnualAdapter] bootstrap slots=', slots, 'approver=', approverInfo); } }catch(e){}
    if(window.ExternalSlots && window.ExternalSlots.fillSlots){
      window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers });
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 200);
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 800);
    }

    if(window.ApproverIntegration && window.ApproverIntegration.renderApprovalLine){
      try{ if(window.__FORM_DEBUG__){ console.log('[AnnualAdapter] renderApprovalLine initial'); } }catch(e){}
      window.ApproverIntegration.renderApprovalLine(approverInfo||{});
      setTimeout(function(){ window.ApproverIntegration.renderApprovalLine(approverInfo||{}); }, 300);

      // 부족하면 API 호출
      if(!approverInfo || !approverInfo.approvers || !approverInfo.approvers.length){
        var pid = (slots && (slots.mst_pid || slots.mstPid)) || getPidFromPath();
        var drafterId = (slots && (slots.drafter_id || slots.drafterId)) || null;
        if(window.ApproverIntegration.fetchApproverInfo && pid){
          try{ if(window.__FORM_DEBUG__){ console.log('[AnnualAdapter] fetchApproverInfo pid=', pid, 'drafterId=', drafterId); } }catch(e){}
          var updated = await window.ApproverIntegration.fetchApproverInfo({ mstPid: pid, drafterId: drafterId });
          try{ if(window.__FORM_DEBUG__){ console.log('[AnnualAdapter] fetched approver=', updated); } }catch(e){}
          if(updated){ window.ApproverIntegration.renderApprovalLine(updated); }
        }
      }
    }

    // slots가 없고 leaveType이 비정규화 값이면 현재 값 기반으로 보정
    try{
      if(!slots){
        var sel = document.getElementById('leaveType') || document.querySelector('[name="leaveType"]');
        if(sel && sel.tagName==='SELECT' && sel.value){
          var v = normalizeLeaveType(sel.value);
          if(v !== sel.value){ sel.value = v; try{ if(window.jQuery && jQuery.fn && jQuery.fn.niceSelect){ jQuery(sel).val(v).trigger('change'); jQuery(sel).niceSelect('update'); }}catch(e){} }
        }
      }
    }catch(e){}
  }

  window.AnnualLeaveAdapter = { bootstrap: bootstrapAnnualLeave };
})();

