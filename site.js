(function(){
  "use strict";
  // Translations: translated pages set window.TE_L10N (tools/i18n). English is the fallback.
  var LX=window.TE_L10N||{};
  function L(k,en,v){var s=(LX[k]!=null?LX[k]:en);if(v){Object.keys(v).forEach(function(n){s=s.split("{"+n+"}").join(v[n]);});}return s;}
  // Fade-up on scroll. Skipped entirely when the visitor prefers reduced motion.
  var rmq=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if(!rmq&&"IntersectionObserver" in window){
    document.documentElement.classList.add("js");
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");io.unobserve(e.target);}});},{rootMargin:"0px 0px -8% 0px"});
    document.querySelectorAll("main section:not(.hero):not(.trust-strip):not(.guide-hero):not(.help-hero) .wrap > *").forEach(function(el){el.classList.add("reveal");io.observe(el);});
  }
  // Pre-launch sign-up: no provider yet, so nothing is sent anywhere.
  document.querySelectorAll("form.signup").forEach(function(f){f.addEventListener("submit",function(e){e.preventDefault();});});
  // Hero video: pause control + respect reduced motion
  var v=document.getElementById("heroVideo"),mb=document.getElementById("motionBtn");
  if(v&&mb){
    var rm=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function setP(p){ if(p){v.pause();mb.textContent=L("playVideo","Play video");mb.setAttribute("aria-pressed","true");} else {v.play();mb.textContent=L("pauseVideo","Pause video");mb.setAttribute("aria-pressed","false");} }
    if(rm){ v.removeAttribute("autoplay"); setP(true); }
    mb.addEventListener("click",function(){ setP(!v.paused); });
  }

  // Sample checker (brief 4.2a). Peter: re-check against the app's data before launch.
  var PP={MY:L("pp_MY","Malaysia"),US:L("pp_US","United States"),IN:L("pp_IN","India"),VN:L("pp_VN","Vietnam")};
  var TO={JP:L("to_JP","Japan"),TH:L("to_TH","Thailand"),GB:L("to_GB","United Kingdom"),KR:L("to_KR","South Korea"),US:L("to_US","United States")};
  var M={VN:{JP:"V",TH:"F30",GB:"V",KR:"V",US:"V"},US:{JP:"F90",TH:"F30",GB:"T180",KR:"F90",US:"own"},IN:{JP:"E90",TH:"F30",GB:"V",KR:"V",US:"V"},MY:{JP:"F90",TH:"F30",GB:"T180",KR:"T90",US:"V"}};
  var FORM={JP:[L("form_JP","Visit Japan Web"),L("note_JP","Optional. Register before you fly. TripEase keeps your passport and trip details ready to copy across.")],TH:[L("form_TH","Thailand Digital Arrival Card (TDAC)"),L("note_TH","Required for every visitor. Free on the official site; submit within 3 days before you arrive.")],GB:[L("form_GB","UK Electronic Travel Authorisation"),L("note_GB","Apply on GOV.UK before you travel if your passport needs one.")],KR:[L("form_KR","Korea e-Arrival Card"),L("note_KR","Submit online up to 3 days before arrival. Some passports also need a K-ETA.")],US:[L("form_US","ESTA"),L("note_US","Required for Visa Waiver Program passports before you board.")]};
  var st={pp:"MY",to:"JP"};
  function $(id){return document.getElementById(id);}
  function render(){
    if(!$("mCode"))return;
    var r=M[st.pp][st.to],c=r[0],d=r.slice(1),o;
    if(r==="own")o=["s-home",L("home_k","Welcome home"),L("home_t","Your own country"),L("home_b","No visa needed.")];
    else if(c==="F")o=["s-ok",L("ok_k","You can go"),L("ok_t","Visa-free"),L("ok_b","Stay up to {d} days as a visitor.",{d:d})];
    else if(c==="T")o=["s-warn",L("warn_k","Before you fly"),L("eta_t","Travel authorisation needed"),L("eta_b","Apply online before you board; visits up to {d} days.",{d:d})];
    else if(c==="E")o=["s-warn",L("warn_k","Before you fly"),L("evisa_t","eVisa"),L("evisa_b","Apply on the official portal; stays up to {d} days.",{d:d})];
    else o=["s-stop",L("stop_k","Plan ahead"),L("stop_t","Visa required"),L("stop_b","Apply through the embassy or official visa site well before travel.")];
    $("mCode").textContent=L("entry","ENTRY · {c}",{c:st.to}); $("mDest").textContent=TO[st.to]; $("mPp").textContent=L("onPassport","On your {p} passport",{p:PP[st.pp]});
    $("mStatus").className="status "+o[0]; $("mK").textContent=o[1]; $("mT").textContent=o[2]; $("mB").textContent=o[3];
    $("mForm").textContent=FORM[st.to][0]; $("mNote").textContent=FORM[st.to][1];
  }
  function pills(group,data){
    var box=document.querySelector('[data-group="'+group+'"]'); if(!box)return;
    Object.keys(data).forEach(function(k){
      var b=document.createElement("button"); b.type="button"; b.className="pill"; b.textContent=data[k];
      b.setAttribute("aria-pressed",String(st[group]===k));
      b.addEventListener("click",function(){ st[group]=k; box.querySelectorAll(".pill").forEach(function(x){x.setAttribute("aria-pressed","false");}); b.setAttribute("aria-pressed","true"); render(); });
      box.appendChild(b);
    });
  }
  pills("pp",PP); pills("to",TO); render();

  // Pricing toggle
  var tg=document.querySelectorAll("[data-period]");
  tg.forEach(function(b){ b.addEventListener("click",function(){
    tg.forEach(function(x){x.setAttribute("aria-pressed","false");}); b.setAttribute("aria-pressed","true");
    var y=b.getAttribute("data-period")==="year";
    $("proPrice").innerHTML=y?L("priceYear","US$29.99 <span>per year</span>"):L("priceMonth","US$4.99 <span>per month</span>");
    $("proNote").textContent=y?L("noteYear","That's about $2.50 a month."):L("noteMonth","Switch to yearly any time.");
  });});

  // Forms: static UI only. Endpoints are placeholders until a backend is approved.
  function wire(id,msgId,ok,check){
    var f=$(id); if(!f)return;
    f.addEventListener("submit",function(e){
      e.preventDefault(); var m=$(msgId);
      if(!f.checkValidity()){ m.textContent=L("checkField","Please check the highlighted field."); f.reportValidity&&f.reportValidity(); return; }
      if(check){ var err=check(f); if(err){ m.textContent=err; return; } }
      var ep=f.getAttribute("action")||"";
      if(!ep||ep.charAt(0)==="["){ m.textContent=L("signupSoon","Sign-up opens soon."); return; }
      fetch(ep,{method:"POST",body:new FormData(f)}).then(function(r){ m.textContent=r.ok?ok:L("wentWrong","Something went wrong. Please try again."); if(r.ok)f.reset(); }).catch(function(){ m.textContent=L("wentWrong","Something went wrong. Please try again."); });
    });
  }
  wire("report","rp-msg","Thanks, we'll check it against the official source.",function(f){
    var t=(f.details.value+" "+f.link.value);
    if(/passport\s*(no|number|#)?\s*[:#]?\s*[A-Z0-9]{6,9}\b/i.test(t)) return "Please remove the passport number. We only need the rule.";
    if(t.length>4000) return "Please keep it under 4,000 characters.";
  });

  // Help search (client-side)
  var q=$("helpSearch");
  if(q){ q.addEventListener("input",function(){
    var s=q.value.trim().toLowerCase();
    document.querySelectorAll(".topic details").forEach(function(d){ var hit=!s||d.textContent.toLowerCase().indexOf(s)>-1; d.hidden=!hit; if(s&&hit)d.open=true; });
    var n=document.querySelectorAll(".topic details:not([hidden])").length; $("searchCount").textContent=s?(n+" matching answer"+(n===1?"":"s")):"";
  });}

  // Data status dates
  var tb=$("statusBody");
  if(tb){ fetch("data/status.json").then(function(r){return r.json();}).then(function(d){
    tb.innerHTML=""; d.sources.forEach(function(s){ var tr=document.createElement("tr"); [s.name,s.refreshed,s.last].forEach(function(x){var td=document.createElement("td"); td.textContent=x; tr.appendChild(td);}); tb.appendChild(tr); });
  }).catch(function(){}); }
})();
