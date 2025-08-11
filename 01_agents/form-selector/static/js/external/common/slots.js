(function(){
  function queryByIdOrName(id){
    // 우선 정확 일치 → 입력 계열만 허용
    var el = document.getElementById(id) || document.querySelector('[name="'+id+'"]');
    if(el && (el.tagName==='INPUT' || el.tagName==='TEXTAREA' || el.tagName==='SELECT')) return el;
    // 부분 일치는 입력 계열로 한정해 래퍼/컨테이너를 파괴하지 않도록 함
    el = document.querySelector('input[id*="'+id+'"],input[name*="'+id+'"],select[id*="'+id+'"],select[name*="'+id+'"],textarea[id*="'+id+'"],textarea[name*="'+id+'"]');
    return el || null;
  }
  function setVal(el, value){
    if(!el) return;
    if(!(el.tagName==='INPUT' || el.tagName==='TEXTAREA' || el.tagName==='SELECT')) return; // 입력 계열 외에는 변경하지 않음
    el.value = value != null ? value : '';
    if(el.tagName==='SELECT'){
      try{ el.setAttribute('data-selected', value); }catch(e){}
      try{ if(window.jQuery && jQuery.fn && jQuery.fn.niceSelect){ jQuery(el).val(value).trigger('change'); jQuery(el).niceSelect('update'); } }catch(e){}
    }
    try{ el.dispatchEvent(new Event('input',{bubbles:true})); }catch(e){}
    try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(e){}
  }
  function snakeToCamel(s){ return String(s||'').replace(/_([a-z])/g,function(_,c){return c.toUpperCase();}); }

  /**
   * Fill slots into DOM elements using alias map and per-key normalizers
   * @param {Object} options
   *  - slots: key→value map
   *  - aliasMap: key→[ids]
   *  - normalizers: key→fn(value)
   */
  function fillSlots(options){
    if(!options || !options.slots) return;
    var slots = options.slots || {};
    var aliasMap = options.aliasMap || {};
    var normalizers = options.normalizers || {};

    try{
      Object.keys(slots).forEach(function(key){
        var value = slots[key];
        var ids = [key];
        var camel = snakeToCamel(key);
        if(camel !== key) ids.push(camel);
        if(aliasMap[key]) ids = ids.concat(aliasMap[key]);

        var el=null;
        for(var i=0;i<ids.length;i++){
          el = queryByIdOrName(ids[i]);
          try{ if(window.__FORM_DEBUG__){ console.log('[ExternalSlots] try ids['+i+']=', ids[i], 'found=', !!el); } }catch(e){}
          if(el) break;
        }
        if(!el) return;

        var v = value;
        if(normalizers[key]){
          try{ v = normalizers[key](value); }catch(e){}
        }
        try{ if(window.__FORM_DEBUG__){ console.log('[ExternalSlots] set', { key: key, element: { id: el.id, name: el.name, tag: el.tagName }, value: v }); } }catch(e){}
        setVal(el, v);
      });
    }catch(e){}
  }

  window.ExternalSlots = { fillSlots: fillSlots };
})();

