// Minimal telefone mask to produce (XX) XXXXX-XXXX while typing
(function(){
  'use strict';

  function formatDigits(digits){
    if(!digits) return '';
    if(digits.indexOf('55')===0 && digits.length>11) digits = digits.slice(2);
    if(digits.length>11) digits = digits.slice(0,11);
    var d1 = digits.slice(0,2);
    var rest = digits.slice(2);
    if(!d1) return '';
    if(rest.length<=0) return '('+d1+') ';
    if(rest.length<=5) return '('+d1+') '+rest;
    return '('+d1+') '+rest.slice(0,5)+'-'+rest.slice(5);
  }

  function onInput(e){
    var el = e.target;
    if(!el || !el.classList) return;
    if(!el.classList.contains('telefone-mask')) return;
    var raw = el.value || '';
    var digits = raw.replace(/\D/g,'');
    if(digits.indexOf('55')===0 && digits.length>11) digits = digits.slice(2);
    if(digits.length>11) digits = digits.slice(0,11);
    var formatted = formatDigits(digits);
    if(formatted !== raw){
      el.value = formatted;
      try { el.setSelectionRange(el.value.length, el.value.length); } catch (err) {}
    }
  }

  function init(){
    document.addEventListener('input', onInput, false);
    document.addEventListener('paste', function(){ setTimeout(function(){
      document.querySelectorAll('.telefone-mask').forEach(function(el){ el.dispatchEvent(new Event('input')); });
    },0); }, false);
    // format any existing inputs right away
    document.querySelectorAll('.telefone-mask').forEach(function(el){ el.dispatchEvent(new Event('input')); });
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
