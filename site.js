(function(){
  "use strict";
  // Hero video: pause control + respect reduced motion
  var v=document.getElementById("heroVideo"),mb=document.getElementById("motionBtn");
  if(v&&mb){
    var rm=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function setP(p){ if(p){v.pause();mb.textContent="Play video";mb.setAttribute("aria-pressed","true");} else {v.play();mb.textContent="Pause video";mb.setAttribute("aria-pressed","false");} }
    if(rm){ v.removeAttribute("autoplay"); setP(true); }
    mb.addEventListener("click",function(){ setP(!v.paused); });
  }

  // Sample checker (brief 4.2a). Peter: re-check against the app's data before launch.
  var PP={TW:"Taiwan",US:"United States",IN:"India",MY:"Malaysia"};
  var TO={JP:"Japan",TH:"Thailand",GB:"United Kingdom",KR:"South Korea",US:"United States"};
  var M={TW:{JP:"F90",TH:"F30",GB:"T180",KR:"F90",US:"T90"},US:{JP:"F90",TH:"F30",GB:"T180",KR:"F90",US:"own"},IN:{JP:"E90",TH:"F30",GB:"V",KR:"V",US:"V"},MY:{JP:"F90",TH:"F30",GB:"T180",KR:"T90",US:"V"}};
  var FORM={JP:["Visit Japan Web","Optional. Register before you fly and get QR codes for faster immigration and customs."],TH:["Thailand Digital Arrival Card (TDAC)","Required for every visitor. Free on the official site; submit within 3 days before you arrive."],GB:["UK Electronic Travel Authorisation","Apply on GOV.UK before you travel if your passport needs one."],KR:["Korea e-Arrival Card","Submit online up to 3 days before arrival. Some passports also need a K-ETA."],US:["ESTA","Required for Visa Waiver Program passports before you board."]};
  var st={pp:"TW",to:"JP"};
  function $(id){return document.getElementById(id);}
  function render(){
    if(!$("mCode"))return;
    var r=M[st.pp][st.to],c=r[0],d=r.slice(1),o;
    if(r==="own")o=["s-home","Welcome home","Your own country","No visa needed."];
    else if(c==="F")o=["s-ok","You can go","Visa-free","Stay up to "+d+" days as a visitor."];
    else if(c==="T")o=["s-warn","Before you fly","Travel authorisation needed","Apply online before you board; visits up to "+d+" days."];
    else if(c==="E")o=["s-warn","Before you fly","eVisa","Apply on the official portal; stays up to "+d+" days."];
    else o=["s-stop","Plan ahead","Visa required","Apply through the embassy or official visa site well before travel."];
    $("mCode").textContent="ENTRY · "+st.to; $("mDest").textContent=TO[st.to]; $("mPp").textContent="On your "+PP[st.pp]+" passport";
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
    $("proPrice").innerHTML=y?'US$19.99 <span>per year</span>':'US$2.99 <span>per month</span>';
    $("proNote").textContent=y?"That's about $1.67 a month.":"Switch to yearly any time.";
  });});

  // Forms: static UI only. Endpoints are placeholders until a backend is approved.
  function wire(id,msgId,ok,check){
    var f=$(id); if(!f)return;
    f.addEventListener("submit",function(e){
      e.preventDefault(); var m=$(msgId);
      if(!f.checkValidity()){ m.textContent="Please check the highlighted field."; f.reportValidity&&f.reportValidity(); return; }
      if(check){ var err=check(f); if(err){ m.textContent=err; return; } }
      var ep=f.getAttribute("action")||"";
      if(!ep||ep.charAt(0)==="["){ m.innerHTML='This form isn\u2019t connected yet. Please email <a href="mailto:support@tripeaseapp.com">support@tripeaseapp.com</a> for now.'; return; }
      fetch(ep,{method:"POST",body:new FormData(f)}).then(function(r){ m.textContent=r.ok?ok:"Something went wrong. Please try again."; if(r.ok)f.reset(); }).catch(function(){ m.textContent="Something went wrong. Please try again."; });
    });
  }
  wire("waitlist","wl-msg","You're on the list. One email on launch day.");
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
