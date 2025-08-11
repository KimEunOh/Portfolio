(function(){
  var SUBMIT_BASE = '';
  try{ SUBMIT_BASE = String(window.__FORM_SUBMIT_BASE__ || '').replace(/\/$/, ''); }catch(e){}
  function getQueryParam(name){
    try{ var url = new URL(window.location.href); return url.searchParams.get(name); }catch(e){ return null; }
  }

  function getMstPid(){
    try{
      var fromGlobal = (typeof window.__MSTPID__ !== 'undefined' && window.__MSTPID__!=null) ? Number(window.__MSTPID__) : null;
      if(fromGlobal) return Number(fromGlobal);
      var fromSlots = (window.__FORM_SLOTS__ && (window.__FORM_SLOTS__.mst_pid || window.__FORM_SLOTS__.mstPid)) || null;
      if(fromSlots) return Number(fromSlots);
      var m = window.location.pathname.match(/\/master\/(\d+)/);
      if(m && m[1]) return Number(m[1]);
      var qp = getQueryParam('mstPid') || getQueryParam('pid');
      if(qp) return Number(qp);
    }catch(e){}
    return null;
  }

  function extractDrafterIdFromDom(){
    try{
      var el = document.querySelector('#drafterName, .approval_line .draft .name');
      if(!el) return null;
      var txt = (el.textContent || '').trim();
      var m = txt.match(/(\d{4,})/); // 숫자 ID 추출
      return m && m[1] ? m[1] : null;
    }catch(e){ return null; }
  }

  var PID_TO_FORM_TYPE = {
    1: 'annual_leave',
    3: 'dinner_expense',
    4: 'transportation_expense',
    5: 'dispatch_businesstrip_report',
    6: 'inventory_purchase_report',
    7: 'purchase_approval_form',
    8: 'personal_expense_report',
    9: 'corporate_card_statement',
    10: 'resignation_letter'
  };

  function getFormType(){
    var pid = getMstPid();
    if(pid && PID_TO_FORM_TYPE[pid]) return PID_TO_FORM_TYPE[pid];
    // fallback: 사용자가 슬롯에 english_id를 전달한 경우
    try{ if(window.__FORM_SLOTS__ && window.__FORM_SLOTS__.form_type){ return String(window.__FORM_SLOTS__.form_type); } }catch(e){}
    return null;
  }

  function serializeForm(form){
    var data = {};
    if(!form) return data;
    var elements = form.querySelectorAll('input, select, textarea');
    elements.forEach(function(el){
      if(!el.name && !el.id) return;
      var key = el.name || el.id;
      var value = null;
      if(el.tagName === 'SELECT'){
        if(el.multiple){
          value = Array.from(el.selectedOptions).map(function(o){ return o.value; });
        } else {
          value = el.value;
        }
      } else if (el.type === 'checkbox'){
        if(!data.hasOwnProperty(key)) data[key] = [];
        if(el.checked) data[key].push(el.value || true);
        return; // 조기 반환으로 아래 공통 처리 스킵
      } else if (el.type === 'radio'){
        if(el.checked){ value = el.value; } else { return; }
      } else {
        value = el.value;
      }

      if(data.hasOwnProperty(key)){
        // 동일 name이 여러 개인 경우 배열로 누적
        if(Array.isArray(data[key])){ data[key].push(value); }
        else { data[key] = [data[key], value]; }
      } else {
        data[key] = value;
      }
    });
    return data;
  }

  async function submitFormData(opts){
    var form = opts && opts.form ? opts.form : (document.querySelector('.form_area form') || document.querySelector('form'));
    if(!form){ alert('제출할 폼을 찾지 못했습니다.'); return; }

    var formType = getFormType();
    if(!formType){ alert('폼 종류를 확인할 수 없습니다. (mstPid 누락)'); return; }

    var formData = serializeForm(form);
    try{
      try{ if(window.__FORM_DEBUG__){ console.log('[FormSubmit] formType=', formType, 'serialized=', formData); } }catch(e){}
      // drafterId 보강: 전역/슬롯/쿼리에서 추론
      var globalDrafter = (typeof window.__DRAFTER_ID__ !== 'undefined' && window.__DRAFTER_ID__!=null) ? String(window.__DRAFTER_ID__) : null;
      var slotDrafter = (window.__FORM_SLOTS__ && (window.__FORM_SLOTS__.drafterId || window.__FORM_SLOTS__.drafter_id)) || null;
      var qpDrafter = getQueryParam('drafterId');
      var domDrafter = extractDrafterIdFromDom();
      if(!formData.drafterId && (globalDrafter || slotDrafter || qpDrafter || domDrafter)){
        formData.drafterId = String(globalDrafter || slotDrafter || qpDrafter || domDrafter);
      }
      // approvers 보강: 전역 결재 정보에서 가져오기
      if(!formData.approvers && window.__APPROVER_INFO__ && Array.isArray(window.__APPROVER_INFO__.approvers)){
        formData.approvers = window.__APPROVER_INFO__.approvers;
      }
    }catch(e){}

    try{
      var url = (SUBMIT_BASE ? (SUBMIT_BASE + '/submit-form') : '/submit-form');
      try{ console.log('[FormSubmit] submit url =', url, 'origin =', window.location.origin, 'base =', SUBMIT_BASE); }catch(e){}
      try{ if(window.__FORM_DEBUG__){ console.log('[FormSubmit] payload preview =', { form_type: formType, form_data: formData }); } }catch(e){}
      var resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ form_type: formType, form_data: formData })
      });
      if(!resp.ok){
        var text = await resp.text();
        throw new Error('제출 실패: ' + text);
      }
      var json = await resp.json();
      alert('제출 성공\n' + JSON.stringify(json));
      return json;
    } catch(e){
      console.error('[FormSubmit] submit error:', e);
      alert('제출 중 오류가 발생했습니다. 콘솔을 확인하세요.');
    }
  }

  function findSubmitButtons(){
    // 공통 스타일 기준으로 탐색
    var selectors = [
      '.btn_area .btn.fill_primary',
      'button.btn.fill_primary',
      'button[type="submit"]'
    ];
    var buttons = [];
    selectors.forEach(function(sel){
      document.querySelectorAll(sel).forEach(function(b){ buttons.push(b); });
    });
    // 중복 제거
    return Array.from(new Set(buttons));
  }

  function bindSubmit(){
    var buttons = findSubmitButtons();
    try{ console.log('[FormSubmit] binding buttons count =', buttons.length); }catch(e){}
    buttons.forEach(function(btn){
      if(btn.dataset.formSubmitBound === '1') return;
      btn.addEventListener('click', function(ev){
        try{ console.log('[FormSubmit] click detected on', btn); }catch(e){}
        ev.preventDefault();
        var form = btn.closest('form') || document.querySelector('.form_area form') || document.querySelector('form');
        submitFormData({ form: form });
      });
      btn.dataset.formSubmitBound = '1';
    });

    // 위 바인딩이 실패했을 때를 대비한 위임 핸들러 (동적 렌더 대응)
    if(!document._formSubmitDelegated){
      document.addEventListener('click', function(e){
        var t = e.target;
        if(!t) return;
        var matches = function(el){
          try{
            return el.matches && (el.matches('.btn_area .btn.fill_primary') || el.matches('button.btn.fill_primary') || el.matches('button[type="submit"]'));
          }catch(err){ return false; }
        };
        var el = t;
        while(el && el !== document){
          if(matches(el)){
            try{ console.log('[FormSubmit] delegated click detected on', el); }catch(_){}
            e.preventDefault();
            var form = el.closest('form') || document.querySelector('.form_area form') || document.querySelector('form');
            submitFormData({ form: form });
            break;
          }
          el = el.parentElement;
        }
      }, true);
      document._formSubmitDelegated = true;
    }
  }

  function bootstrap(){
    bindSubmit();
    setTimeout(bindSubmit, 300);
    setTimeout(bindSubmit, 1000);
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }

  window.FormSubmit = { submit: submitFormData, bind: bindSubmit };
})();

