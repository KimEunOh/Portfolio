(function(){
  function queryByIdOrName(id){
    return document.getElementById(id) || document.querySelector('[name="'+id+'"]') || document.querySelector('[id*="'+id+'"],[name*="'+id+'"]');
  }
  function setVal(el, value){
    if(!el) return;
    if(el.tagName==='INPUT' || el.tagName==='TEXTAREA' || el.tagName==='SELECT'){
      el.value = value != null ? value : '';
      if(el.tagName==='SELECT'){
        try{ el.setAttribute('data-selected', value); }catch(e){}
        try{ if(window.jQuery && jQuery.fn && jQuery.fn.niceSelect){ jQuery(el).val(value).trigger('change'); jQuery(el).niceSelect('update'); } }catch(e){}
      }
      try{ el.dispatchEvent(new Event('input',{bubbles:true})); }catch(e){}
      try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(e){}
    } else {
      el.textContent = String(value != null ? value : '');
    }
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
          if(el) break;
        }
        if(!el) return;

        var v = value;
        if(normalizers[key]){
          try{ v = normalizers[key](value); }catch(e){}
        }
        setVal(el, v);
      });
    }catch(e){}
  }

  window.ExternalSlots = { fillSlots: fillSlots };
})();

