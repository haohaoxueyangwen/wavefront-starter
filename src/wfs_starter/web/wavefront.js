"use strict";
// Display and interaction only; original workers perform all numerical analysis.
if(APP==="wavefront"){
let zoom=1,drag=null,images=[],index=0,scale=1,pan=null;
const fmt=v=>v==="Infinity"?"∞":v==="-Infinity"?"−∞":typeof v==="number"?v.toPrecision(7):String(v??"—");
function roiZoom(v){zoom=Math.max(1,Math.min(12,v));$("previewCanvas").style.width=zoom*100+"%";$("previewCanvas").style.maxWidth="none";$("roiZoomLabel").textContent=Math.round(zoom*100)+"%";}
function formChanged(){
 const full=selectedMode==="zernike_full",e=Number(config.photon_energy_kev);
 $("wavelength").textContent=full&&e>0?`λ = ${(1.2398419843320026/e).toPrecision(8)} nm = ${(0.0012398419843320026/e).toPrecision(8)} µm（由能量计算）`:"";
 $("analysisCorrections").hidden=!full;$("roiTools").hidden=!full;
 const centerInput=$("param-center_xy_px");
 if(full&&centerInput&&!$("centerX")){
  centerInput.hidden=true;
  const fields=document.createElement("div");fields.className="fields two";
  for(const [i,id,label] of [[0,"centerX","圆心 X · px"],[1,"centerY","圆心 Y · px"]]){
   const wrap=document.createElement("div"),caption=document.createElement("span"),input=document.createElement("input");caption.textContent=label;
   input.type="number";input.step="any";input.min="0";input.id=id;input.setAttribute("aria-label",label);input.value=config.center_xy_px?.[i]??"";
   input.oninput=()=>{const x=$("centerX").value,y=$("centerY").value;centerInput.value=x!==""&&y!==""?JSON.stringify([Number(x),Number(y)]):"";centerInput.dispatchEvent(new Event("input",{bubbles:true}));};
   wrap.append(caption,input);fields.append(wrap);
  }centerInput.parentElement.append(fields);
 }
 for(const option of $("param-phase_unit")?.options||[])option.disabled=["zernike_full","surface"].includes(selectedMode)&&option.value==="m";
 if(selectedMode==="surface"){
  const threshold=$("param-threshold_value");if(threshold)threshold.disabled=config.threshold_mode!=="custom";
  const delta=$("param-delta");if(delta)delta.disabled=!config.use_delta;
 }
 if(full){for(const [v,label] of [["circle","拖画圆瞳"],["move","移动圆瞳"],["pan","平移视图"]])if(![...$("pickTarget").options].some(o=>o.value===v))$("pickTarget").add(new Option(label,v));for(const o of $("pickTarget").options)o.hidden=["x","y"].includes(o.value);$("previewHelp").textContent="拖画圆瞳、移动圆心或设置半径；可输入小数。缩放仅影响显示，选区使用原数组坐标。";}
}
document.addEventListener("input",e=>{if(["photon_energy_kev","threshold_mode","use_delta"].includes(e.target.dataset.key))formChanged();});
function inputStats(s){if(!s)return;$("inputStats").textContent=`范围 ${fmt(s.minimum)} … ${fmt(s.maximum)}；均值 ${fmt(s.mean)}；标准差 ${fmt(s.std)}；有限点 ${s.finite_points}/${s.total_points}。预览灰度伸缩不改变相位。`;roiZoom(1);setTimeout(()=>{formChanged();if(selectedMode==="zernike_full")$("pickTarget").value="circle";},0);}
$("roiZoomIn").onclick=()=>roiZoom(zoom*1.3);$("roiZoomOut").onclick=()=>roiZoom(zoom/1.3);$("roiReset").onclick=()=>{roiZoom(1);$("roiViewport").scrollTo(0,0);};
$("roiViewport").addEventListener("wheel",e=>{if(selectedMode!=="zernike_full")return;e.preventDefault();roiZoom(zoom*(e.deltaY<0?1.15:1/1.15));},{passive:false});
function point(e){const r=$("previewCanvas").getBoundingClientRect();return [(e.clientX-r.left)*previewShape[1]/r.width,(e.clientY-r.top)*previewShape[0]/r.height];}
$("previewCanvas").addEventListener("pointerdown",e=>{
 if(selectedMode!=="zernike_full"||!previewShape||e.button!==0)return;
 try{collect();}catch(error){say(error.message,true);return;}
 const mode=$("pickTarget").value,p=point(e),view=$("roiViewport");
 if(["radius","move"].includes(mode)&&!config.center_xy_px){say("请先选择圆心。",true);return;}
 drag={mode,p,start:[e.clientX,e.clientY],scroll:[view.scrollLeft,view.scrollTop],center:config.center_xy_px?.slice()};e.currentTarget.setPointerCapture(e.pointerId);
 if(["circle","center"].includes(mode))config.center_xy_px=p;if(mode==="circle")config.radius_px=1;if(mode==="radius")config.radius_px=Math.hypot(p[0]-config.center_xy_px[0],p[1]-config.center_xy_px[1]);drawPreview();e.preventDefault();
});
$("previewCanvas").addEventListener("pointermove",e=>{
 if(!drag)return;const p=point(e);
 if(drag.mode==="pan"){$("roiViewport").scrollLeft=drag.scroll[0]-(e.clientX-drag.start[0]);$("roiViewport").scrollTop=drag.scroll[1]-(e.clientY-drag.start[1]);return;}
 if(["circle","radius"].includes(drag.mode))config.radius_px=Math.max(.001,Math.hypot(p[0]-config.center_xy_px[0],p[1]-config.center_xy_px[1]));
 if(drag.mode==="move")config.center_xy_px=[Math.max(0,Math.min(previewShape[1]-1,drag.center[0]+p[0]-drag.p[0])),Math.max(0,Math.min(previewShape[0]-1,drag.center[1]+p[1]-drag.p[1]))];drawPreview();
});
function finish(){if(!drag)return;drag=null;render();drawPreview();persist();}
$("previewCanvas").addEventListener("pointerup",finish);$("previewCanvas").addEventListener("pointercancel",finish);
function viewerZoom(v){scale=Math.max(.25,Math.min(16,v));$("viewerImage").style.width=scale*100+"%";$("viewerZoom").textContent=Math.round(scale*100)+"%";}
function show(i){index=(i+images.length)%images.length;const item=images[index];$("viewerTitle").textContent=item.file.split("/").at(-1);$("viewerImage").src=item.url;$("viewerDownload").href=item.url;$("viewerDownload").download=item.file.split("/").at(-1);$("viewerPage").textContent=`${index+1} / ${images.length}`;viewerZoom(1);$("viewerViewport").scrollTo(0,0);}
$("viewerClose").onclick=()=>$("resultViewer").close();$("viewerPrev").onclick=()=>show(index-1);$("viewerNext").onclick=()=>show(index+1);$("viewerPlus").onclick=()=>viewerZoom(scale*1.3);$("viewerMinus").onclick=()=>viewerZoom(scale/1.3);$("viewerReset").onclick=()=>{viewerZoom(1);$("viewerViewport").scrollTo(0,0);};
$("viewerViewport").addEventListener("wheel",e=>{e.preventDefault();viewerZoom(scale*(e.deltaY<0?1.15:1/1.15));},{passive:false});
$("viewerImage").draggable=false;$("viewerViewport").onpointerdown=e=>{pan={x:e.clientX,y:e.clientY,left:e.currentTarget.scrollLeft,top:e.currentTarget.scrollTop};e.currentTarget.setPointerCapture(e.pointerId);};$("viewerViewport").onpointermove=e=>{if(pan){e.currentTarget.scrollLeft=pan.left-(e.clientX-pan.x);e.currentTarget.scrollTop=pan.top-(e.clientY-pan.y);}};$("viewerViewport").onpointerup=()=>pan=null;$("viewerViewport").onpointercancel=()=>pan=null;
$("resultViewer").addEventListener("keydown",e=>{if(e.key==="ArrowLeft")show(index-1);if(e.key==="ArrowRight")show(index+1);});
function cell(text,tag="td"){const node=document.createElement(tag);node.textContent=text;return node;}
function summary(data){
 const box=$("analysisSummary");box.replaceChildren();if(!data)return;const heading=document.createElement("h3");heading.textContent="定量分析 · 圆瞳内";box.append(heading);const table=document.createElement("table");table.className="analysis-table";
 for(const [label,pv,rms] of [["整体波前","pv_original_rad","rms_original_rad"],[`去除径向阶数 0–${data.max_order_remove} 后`,"pv_higher_order_rad","rms_higher_order_rad"],["全部拟合后的残差","pv_fitting_residual_rad","rms_fitting_residual_rad"]]){const row=document.createElement("tr");row.append(cell(label,"th"),cell(`PV ${fmt(data[pv])} rad`),cell(`RMS ${fmt(data[rms])} rad`));table.append(row);}
 const row=document.createElement("tr");row.append(cell("曲率半径","th"),cell(`Rx ${fmt(data.roc_x_mm)} mm · Ry ${fmt(data.roc_y_mm)} mm`),cell(`平均 ${fmt(data.roc_mean_mm)} mm`));table.append(row);box.append(table);
 const note=document.createElement("p");note.className="help";note.textContent=`${data.terms} 项 · ROI ${data.roi_points} 点 · 圆心 [${data.center_xy_px.map(fmt).join(", ")}] · 半径 ${fmt(data.radius_px)} px。RMS 沿用标准差定义；曲率沿用 j4/j6 的固定 X/Y 公式。`;box.append(note);
 const details=document.createElement("details");details.open=true;const title=document.createElement("summary");title.textContent=`全部 ${data.coefficients.length} 项系数（Noll 编号；rad / waves）`;const coefficients=document.createElement("table");coefficients.className="analysis-table";const head=document.createElement("tr");for(const name of ["j","(n,m)","rad","waves","低阶去除"])head.append(cell(name,"th"));coefficients.append(head);
 for(const item of data.coefficients){const line=document.createElement("tr");for(const value of [item.j,`(${item.n},${item.m})`,fmt(item.rad),fmt(item.waves),item.removed?"是":"否"])line.append(cell(value));coefficients.append(line);}const scroll=document.createElement("div");scroll.className="coefficient-scroll";scroll.append(coefficients);details.append(title,scroll);box.append(details);
}
function jobChanged(job){const p=job.progress;$("analysisProgress").hidden=!p;if(p){$("progressBar").value=p.percent;$("progressLabel").textContent=`${p.percent}% · ${p.message}`;}summary(job.status==="succeeded"?job.summary:null);images=job.files.filter(f=>f.endsWith(".png")).map(file=>({file,url:resultUrl(job,file)}));for(const [i,tile] of [...$("gallery").children].entries()){tile.tabIndex=0;tile.title="查看原图、缩放和平移";const open=()=>{show(i);$("resultViewer").showModal();};tile.onclick=open;tile.onkeydown=e=>{if(e.key==="Enter")open();};}}
window.WFSWavefront={formChanged,inputStats,jobChanged};
const openFolder=document.createElement("button");openFolder.textContent="打开结果文件夹";openFolder.onclick=async()=>{try{if(!viewed)throw Error("请先选择一条任务记录。");await request("/api/open-output",{id:viewed});}catch(error){say(error.message,true);}};$("logPanel").append(openFolder);
}
