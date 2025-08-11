(function(){
  // Alias map for dinner expense
  var aliasMap = {
    work_location: ['workLocation'],
    overtime_time: ['overtimeTime'],
    bank_account_for_deposit: ['bankAccountForDeposit'],
    dinner_date: ['useYmd','dinnerDate'],
    reason: ['workContent','work_content']
  };

  var normalizers = {
    // Add if time normalization or amount normalization is needed later
  };

  function getPidFromPath(){
    try{ var m = window.location.pathname.match(/\/master\/(\d+)/); if(m&&m[1]) return Number(m[1]); }catch(e){}
    return null;
  }

  async function bootstrap(slots, approverInfo){
    try{ if(window.__FORM_DEBUG__){ console.log('[DinnerAdapter] bootstrap slots=', slots, 'approver=', approverInfo); } }catch(e){}
    // 1) Fill slots
    if(window.ExternalSlots && window.ExternalSlots.fillSlots){
      window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers });
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 200);
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 800);
    }

    // 2) Render approval line and possibly fetch if missing
    if(window.ApproverIntegration){
      try{ if(window.__FORM_DEBUG__){ console.log('[DinnerAdapter] renderApprovalLine initial'); } }catch(e){}
      window.ApproverIntegration.renderApprovalLine(approverInfo||{});
      if(!approverInfo || !approverInfo.approvers || !approverInfo.approvers.length){
        var pid = (slots && (slots.mst_pid || slots.mstPid)) || getPidFromPath();
        var drafterId = (slots && (slots.drafter_id || slots.drafterId)) || null;
        if(pid && window.ApproverIntegration.fetchApproverInfo){
          try{ if(window.__FORM_DEBUG__){ console.log('[DinnerAdapter] fetchApproverInfo pid=', pid, 'drafterId=', drafterId); } }catch(e){}
          var info = await window.ApproverIntegration.fetchApproverInfo({ mstPid: pid, drafterId: drafterId });
          try{ if(window.__FORM_DEBUG__){ console.log('[DinnerAdapter] fetched approver=', info); } }catch(e){}
          if(info){ window.ApproverIntegration.renderApprovalLine(info); }
        }
      }
    }
  }

  window.DinnerExpenseAdapter = { bootstrap: bootstrap };
})();

