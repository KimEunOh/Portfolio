(function(){
  // 최소한의 별칭/정규화만 유지 (대부분의 값은 퍼블리싱 폼의 동적 항목에서 수집)
  var aliasMap = {
    notes: ['otherNotes','memo']
  };
  var normalizers = {
    // 현재 별도 정규화 없음
  };

  function getPidFromPath(){
    try{ var m = window.location.pathname.match(/\/master\/(\d+)/); if(m&&m[1]) return Number(m[1]); }catch(e){}
    return null;
  }

  function parseNumber(value){ var n = Number(String(value||'').replace(/[^\d.-]/g,'')); return isNaN(n)?0:n; }

  function collectItems(){
    // 퍼블리싱 템플릿 패턴 지원: amount1, transportType1, origin1, destination1, notes1 ...
    var items = [];
    try{
      // 인덱스를 증가시키며 필드를 스캔 (최대 maxScan)
      var maxScan = 30; var foundAny = false;
      for(var i=1;i<=maxScan;i++){
        var amountEl = document.getElementById('amount'+i) || document.querySelector('[name="amount'+i+'"]');
        var transportEl = document.getElementById('transportType'+i) || document.querySelector('[name="transportType'+i+'"]');
        var originEl = document.getElementById('origin'+i) || document.querySelector('[name="origin'+i+'"]');
        var destinationEl = document.getElementById('destination'+i) || document.querySelector('[name="destination'+i+'"]');
        var notesEl = document.getElementById('notes'+i) || document.querySelector('[name="notes'+i+'"]');
        if(!(amountEl || transportEl || originEl || destinationEl || notesEl)){
          continue;
        }
        foundAny = true;
        var amount = parseNumber(amountEl && amountEl.value);
        var item = {
          transport_type: transportEl ? transportEl.value : '',
          origin: originEl ? originEl.value : '',
          destination: destinationEl ? destinationEl.value : '',
          amount: amount,
          notes: notesEl ? notesEl.value : ''
        };
        if(item.transport_type || item.origin || item.destination || item.amount || item.notes){ items.push(item); }
      }
    }catch(e){ try{ if(window.__FORM_DEBUG__){ console.warn('[TransportationAdapter] collectItems error', e); } }catch(_e){} }
    return items;
  }

  // 숫자에 천단위 구분기호 추가
  function formatComma(n){ try{ var num = parseNumber(n); return num ? num.toLocaleString('ko-KR') : ''; }catch(_){ return String(n||''); } }

  // 슬롯의 items 배열을 퍼블리싱 폼에 채워넣기
  function populateItemsFromSlots(slots){
    try{
      if(!slots || !Array.isArray(slots.items) || !slots.items.length) return;
      var list = document.querySelector('.detail_area ul');
      if(!list) return;
      var need = slots.items.length;
      ensureListItemCount(need);

      // 각 항목 채움
      slots.items.forEach(function(it, idx){
        var i = idx + 1;
        var amountEl = document.getElementById('amount'+i) || list.querySelector('[name="amount'+i+'"]');
        var transportEl = document.getElementById('transportType'+i) || list.querySelector('[name="transportType'+i+'"]');
        var originEl = document.getElementById('origin'+i) || list.querySelector('[name="origin'+i+'"]');
        var destinationEl = document.getElementById('destination'+i) || list.querySelector('[name="destination'+i+'"]');
        var notesEl = document.getElementById('notes'+i) || list.querySelector('[name="notes'+i+'"]');
        if(amountEl){ amountEl.value = formatComma(it.amount); }
        if(transportEl){ transportEl.value = it.transport_type || it.transportType || ''; try{ transportEl.dispatchEvent(new Event('change',{bubbles:true})); }catch(_e){} }
        if(originEl){ originEl.value = it.origin || ''; }
        if(destinationEl){ destinationEl.value = it.destination || ''; }
        if(notesEl){ notesEl.value = it.notes || ''; }
        // 타이틀 보정
        try{ updateBoxTitleForTarget(transportEl || originEl || destinationEl || notesEl); }catch(_e){}
      });
      try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_e){}
    }catch(e){}
  }

  // 목록(li) 개수를 target까지 확보 (퍼블리싱 add 버튼 또는 폴백 복제)
  function ensureListItemCount(target){
    var list = document.querySelector('.detail_area ul');
    if(!list) return;
    var getTopItems = function(ul){ return Array.prototype.filter.call((ul && ul.children)||[], function(el){ return el && el.tagName === 'LI'; }); };
    var addBtn = document.querySelector('.btn_add');
    var maxTarget = Math.min(Number(target)||0, 30);
    var current = getTopItems(list).length;
    for(var step=0; current < maxTarget && step < 40; step++){
      var before = current;
      if(addBtn){ addBtn.click(); }
      current = getTopItems(list).length;
      if(current > before){ continue; }
      // fallback: 직접 복제 + 인덱스 재배치
      var itemsEls = getTopItems(list);
      var last = itemsEls[itemsEls.length-1];
      if(!last) break;
      var clone = last.cloneNode(true);
      // 기존 nice-select 래퍼 제거 및 select 표시 복구
      Array.prototype.forEach.call(clone.querySelectorAll('.nice-select'), function(el){ if(el.parentNode){ el.parentNode.removeChild(el); } });
      Array.prototype.forEach.call(clone.querySelectorAll('select'), function(sel){ sel.removeAttribute('style'); sel.classList.remove('nice-initialized'); });
      var nextIndex = itemsEls.length + 1;
      clone.querySelectorAll('input, select, textarea, label').forEach(function(el){
        ['id','name','for'].forEach(function(attr){
          var v = el.getAttribute && el.getAttribute(attr);
          if(!v) return;
          el.setAttribute(attr, v.replace(/(amount|transportType|origin|destination|notes)\d+/, function(m){ return m.replace(/\d+$/, String(nextIndex)); }));
        });
        if(el.tagName==='INPUT' || el.tagName==='TEXTAREA'){ el.value = ''; }
        if(el.tagName==='SELECT'){ el.value = ''; try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(_){} }
      });
      try{
        var titleP = clone.querySelector('.box_head .tit p');
        if(titleP){ titleP.textContent = '기타'; }
      }catch(_e){}
      list.appendChild(clone);
      current = getTopItems(list).length;
      try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_e){}
    }
  }

  function ensureHiddenItemsField(){
    try{
      var form = document.querySelector('.form_area form') || document.querySelector('form');
      if(!form) return;
      var hidden = form.querySelector('input[name="items"]');
      if(!hidden){ hidden = document.createElement('input'); hidden.type='hidden'; hidden.name='items'; form.appendChild(hidden); }
      var items = collectItems();
      hidden.value = JSON.stringify(items);
      // 총액 필드(totalAmount)가 있으면 합계를 재계산하여 반영
      try{
        var totalField = document.getElementById('totalAmount') || form.querySelector('[name="totalAmount"]');
        if(totalField){
          var sum = 0; items.forEach(function(it){ sum += parseNumber(it.amount); });
          totalField.value = sum.toLocaleString('ko-KR');
        }
      }catch(e){}
      try{ if(window.__FORM_DEBUG__){ console.log('[TransportationAdapter] items updated, count=', items.length); } }catch(e){}
    }catch(e){}
  }

  async function bootstrap(slots, approverInfo){
    if(window.__TRANSPORTATION_ADAPTER_BOOTSTRAPPED__){ return; }
    window.__TRANSPORTATION_ADAPTER_BOOTSTRAPPED__ = true;
    try{ console.log('[TransportationAdapter][DEBUG] bootstrap start. slots=', Object.keys(slots||{}), 'approver=', !!approverInfo); }catch(e){}
    // 1) 기본 슬롯 채우기 (예: notes)
    if(window.ExternalSlots && window.ExternalSlots.fillSlots){
      window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers });
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 200);
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 800);
    }

    // 2) 결재 라인 렌더링 및 필요 시 조회
    if(window.ApproverIntegration){
      try{ if(window.__FORM_DEBUG__){ console.log('[TransportationAdapter] renderApprovalLine'); } }catch(e){}
      try{ console.log('[TransportationAdapter][DEBUG] renderApprovalLine call'); }catch(e){}
      window.ApproverIntegration.renderApprovalLine(approverInfo||{});
      if(!approverInfo || !approverInfo.approvers || !approverInfo.approvers.length){
        var pid = (slots && (slots.mst_pid || slots.mstPid)) || getPidFromPath();
        var drafterId = (slots && (slots.drafter_id || slots.drafterId)) || null;
        if(pid && window.ApproverIntegration.fetchApproverInfo){
           try{ console.log('[TransportationAdapter][DEBUG] fetchApproverInfo'); }catch(e){}
          var info = await window.ApproverIntegration.fetchApproverInfo({ mstPid: pid, drafterId: drafterId });
           try{ console.log('[TransportationAdapter][DEBUG] fetched approver'); }catch(e){}
          if(info){ window.ApproverIntegration.renderApprovalLine(info); }
        }
      }
    }

    // 3) hidden `items` 필드를 지속적으로 최신 상태로 유지
    //    슬롯으로 전달된 items가 있으면 우선 폼에 채움
    try{ console.log('[TransportationAdapter][DEBUG] populateItemsFromSlots'); }catch(_e){}
    try{ populateItemsFromSlots(slots||{}); }catch(_e){}
    try{ console.log('[TransportationAdapter][DEBUG] ensureHiddenItemsField initial'); }catch(_e){}
    ensureHiddenItemsField();
    // 폼 내부 입력 변경 시 반영
    try{
      // 퍼블리싱 입력 필드 변경 감지
      document.addEventListener('input', function(e){
        var t = e && e.target;
        if(!t) return;
        if(t.name && (/^(amount|origin|destination|notes)\d+$/).test(t.name)){
          ensureHiddenItemsField();
        }
        if(t.id && (/^(amount|origin|destination|notes)\d+$/).test(t.id)){
          ensureHiddenItemsField();
        }
      }, true);
      document.addEventListener('change', function(e){
        var t = e && e.target;
        if(!t) return;
        if((t.id && /^transportType\d+$/.test(t.id)) || (t.name && /^transportType\d+$/.test(t.name))){ 
          ensureHiddenItemsField();
          try{ updateBoxTitleForTarget(t); }catch(_e){}
        }
      }, true);

      // 퍼블리싱 DOM의 행 추가/삭제 버튼 처리
      document.addEventListener('click', function(e){
        var btn = e.target;
        if(!btn) return;
        // 행 추가
        if(btn.classList && btn.classList.contains('btn_add')){
          var list = document.querySelector('.detail_area ul');
          if(!list) return;
          // 최상위 자식 li만 대상으로 복제 (nice-select 내부 option li 제외)
          var itemsEls = Array.prototype.filter.call((list && list.children)||[], function(el){ return el && el.tagName === 'LI'; });
          var last = itemsEls[itemsEls.length-1];
          if(!last) return;
          var clone = last.cloneNode(true);
          // 기존 nice-select 래퍼 제거 및 select 표시 복구
          Array.prototype.forEach.call(clone.querySelectorAll('.nice-select'), function(el){ if(el.parentNode){ el.parentNode.removeChild(el); } });
          Array.prototype.forEach.call(clone.querySelectorAll('select'), function(sel){ sel.removeAttribute('style'); sel.classList.remove('nice-initialized'); });
          // 다음 인덱스 계산
          var nextIndex = itemsEls.length + 1;
          // id/name/for 속성의 숫자 인덱스를 갱신하고 값 초기화
          clone.querySelectorAll('input, select, textarea, label').forEach(function(el){
            ['id','name','for'].forEach(function(attr){
              var v = el.getAttribute && el.getAttribute(attr);
              if(v){ el.setAttribute(attr, v.replace(/(amount|transportType|origin|destination|notes)\d+/, function(m){ return m.replace(/\d+$/, String(nextIndex)); })); }
            });
            if(el.tagName==='INPUT' || el.tagName==='TEXTAREA'){ el.value = ''; }
            if(el.tagName==='SELECT'){ el.value = ''; try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(_){} }
          });
          // 타이틀 초기화
          try{
            var titleP = clone.querySelector('.box_head .tit p');
            if(titleP){ titleP.textContent = '기타'; }
          }catch(_e){}
          list.appendChild(clone);
          try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_e){}
          setTimeout(ensureHiddenItemsField, 0);
          e.preventDefault();
          return;
        }
        // 행 삭제
        if(btn.classList && btn.classList.contains('btn_remove')){
          var li = btn.closest('li');
          var list2 = document.querySelector('.detail_area ul');
          if(li && list2 && list2.querySelectorAll('li').length > 1){ li.remove(); setTimeout(ensureHiddenItemsField, 0); }
          e.preventDefault();
          return;
        }
      }, true);
      // 출발/목적지 변경 시 타이틀 보조
      document.addEventListener('input', function(e){
        var t = e && e.target; if(!t) return;
        if((t.id && /^(origin|destination)\d+$/.test(t.id)) || (t.name && /^(origin|destination)\d+$/.test(t.name))){
          try{ updateBoxTitleForTarget(t); }catch(_e){}
        }
      }, true);
    }catch(e){}
  }

  // 각 항목의 상단 타이틀 텍스트를 교통수단 및 출발/목적지로 갱신
  function updateBoxTitleForTarget(target){
    var li = target.closest('li');
    if(!li) return;
    var p = li.querySelector('.box_head .tit p');
    if(!p) return;
    var idxMatch = (target.id||target.name||'').match(/(\d+)$/);
    var i = idxMatch ? idxMatch[1] : '';
    var transport = document.getElementById('transportType'+i) || li.querySelector('[name="transportType'+i+'"]');
    var origin = document.getElementById('origin'+i) || li.querySelector('[name="origin'+i+'"]');
    var destination = document.getElementById('destination'+i) || li.querySelector('[name="destination'+i+'"]');
    var mode = (transport && transport.value) ? transport.value : '기타';
    var o = origin && origin.value ? origin.value : '';
    var d = destination && destination.value ? destination.value : '';
    var route = (o || d) ? (' (' + (o||'') + ' → ' + (d||'') + ')') : '';
    p.textContent = mode + route;
  }

  window.TransportationExpenseAdapter = { bootstrap: bootstrap };
})();

