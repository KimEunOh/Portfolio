(function(){
  function getEnglishFormType(){
    try{
      if(window.__FORM_SLOTS__ && window.__FORM_SLOTS__.form_type){ return String(window.__FORM_SLOTS__.form_type); }
    }catch(e){}
    // heuristic by path
    var path = (window.location.pathname||'').toLowerCase();
    if(/master\/1\b/.test(path)) return 'annual_leave';
    if(/master\/3\b/.test(path)) return 'dinner_expense';
    if(/master\/4\b/.test(path)) return 'transportation_expense';
    if(/master\/5\b/.test(path)) return 'dispatch_businesstrip_report';
    if(/master\/6\b/.test(path)) return 'inventory_purchase_report';
    if(/master\/7\b/.test(path)) return 'purchase_approval_form';
    if(/master\/8\b/.test(path)) return 'personal_expense_report';
    if(/master\/9\b/.test(path)) return 'corporate_card_statement';
    return null;
  }

  function bootstrap(){
    var slots = window.__FORM_SLOTS__ || {};
    var approver = window.__APPROVER_INFO__ || {};
    var ft = getEnglishFormType();
    try{ if(window.__FORM_DEBUG__){ console.log('[AdapterBootstrap] form_type =', ft, 'slots=', slots, 'approver=', approver); } }catch(e){}
    try{
      if(ft === 'annual_leave' && window.AnnualLeaveAdapter){ window.AnnualLeaveAdapter.bootstrap(slots, approver); return; }
      if(ft === 'dinner_expense' && window.DinnerExpenseAdapter){ window.DinnerExpenseAdapter.bootstrap(slots, approver); return; }
      // add other forms here as they are implemented
    }catch(e){}
    try{ if(window.UIReinit){ if(window.__FORM_DEBUG__){ console.log('[AdapterBootstrap] UIReinit schedule'); } window.UIReinit.schedule(); } }catch(e){}
  }

  // start attempts
  var attempts = 0; var timer = setInterval(function(){ attempts++; try{ if(window.__FORM_DEBUG__){ console.log('[AdapterBootstrap] attempt', attempts); } }catch(e){} bootstrap(); if(attempts>20){ clearInterval(timer); } }, 150);
})();

