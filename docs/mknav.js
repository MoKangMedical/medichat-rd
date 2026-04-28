
(function(){
  var projects = [
    {cat:"Core Platform",items:[
      {name:"OPC Homepage",url:"https://mokangmedical.github.io/opc-homepage/",status:"live"},
      {name:"OPC Platform",url:"https://mokangmedical.github.io/opc-platform/",status:"live"},
      {name:"OPC Marketplace",url:"https://mokangmedical.github.io/opc-marketplace/",status:"live"},
      {name:"OPC Alliance",url:"https://mokangmedical.github.io/opc-alliance/",status:"live"}
    ]},
    {cat:"Medical AI",items:[
      {name:"Tianyan",url:"https://mokangmedical.github.io/tianyan/",status:"live"},
      {name:"PharmaSim",url:"https://mokangmedical.github.io/PharmaSim/",status:"live"},
      {name:"DrugMind",url:"https://mokangmedical.github.io/drugmind/",status:"live"},
      {name:"MediChat-RD",url:"https://mokangmedical.github.io/medichat-rd/",status:"beta"},
      {name:"ChroniCare OS",url:"https://mokangmedical.github.io/chronicdiseasemanagement/",status:"live"}
    ]},
    {cat:"Knowledge & Education",items:[
      {name:"Digital Sage",url:"https://mokangmedical.github.io/digital-sage/",status:"live"},
      {name:"Kondratiev Wave",url:"https://mokangmedical.github.io/kondratiev-wave/",status:"live"}
    ]},
    {cat:"Life & Legacy",items:[
      {name:"Cloud Memorial",url:"https://mokangmedical.github.io/cloud-memorial/",status:"live"},
      {name:"Virtual Cell",url:"https://mokangmedical.github.io/virtual-cell/",status:"live"},
      {name:"NarrowGate",url:"https://mokangmedical.github.io/narrowgate/",status:"live"}
    ]}
  ];
  var currentUrl = window.location.href.replace(/\/$/,"");
  var btn = document.createElement("button");
  btn.className = "mknav-toggle";
  btn.innerHTML = "M";
  btn.title = "MoKangMedical Projects";
  var panel = document.createElement("div");
  panel.className = "mknav-panel";
  var html = '<div class="mknav-header"><span class="logo">MoKangMedical</span><span class="sub">14 Projects</span></div>';
  projects.forEach(function(cat){
    html += '<div class="mknav-section"><div class="mknav-section-title">' + cat.cat + '</div>';
    cat.items.forEach(function(p){
      var isActive = currentUrl.indexOf(p.url.replace(/\/$/,"")) !== -1;
      html += '<a href="' + p.url + '" class="mknav-link"' + (isActive?' style="color:#10b981;font-weight:600"':'') + '><span class="dot ' + p.status + '"></span>' + p.name + '</a>';
    });
    html += '</div>';
  });
  html += '<div class="mknav-footer"><a href="https://github.com/MoKangMedical">github.com/MoKangMedical</a></div>';
  panel.innerHTML = html;
  document.body.appendChild(btn);
  document.body.appendChild(panel);
  btn.onclick = function(){panel.classList.toggle("open")};
  document.addEventListener("click",function(e){if(!btn.contains(e.target)&&!panel.contains(e.target))panel.classList.remove("open")});
})();
