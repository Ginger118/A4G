import {useEffect,useRef} from 'react';
import {ThemeSwitch} from '../theme';
import './account.css';
type Props={theme:'dark'|'light';toggleTheme:()=>void;name:string;avatarText:string;workspaceLabel:string;model:string;mode:'live'|'demo';liveAvailable:boolean;busy:boolean;compact:boolean;onMode:(mode:'live'|'demo')=>void;onGuide:()=>void;onSettings:()=>void;onLogout:()=>void;onClose:(restore?:boolean)=>void};
export default function AccountPanel(p:Props){
 const panel=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  panel.current?.querySelector<HTMLButtonElement>('button')?.focus();
  const click=(e:PointerEvent)=>{const target=e.target as Element;if(!panel.current?.contains(target)&&!target.closest('[data-account-trigger]'))p.onClose(false);};
  const key=(e:KeyboardEvent)=>{if(e.key==='Escape'){e.preventDefault();p.onClose(true);}};
  document.addEventListener('pointerdown',click);document.addEventListener('keydown',key);
  return()=>{document.removeEventListener('pointerdown',click);document.removeEventListener('keydown',key);};
 },[]);
 return <div id="account-panel" ref={panel} role="dialog" aria-label="用户菜单" className={'account-panel '+(p.compact?'account-panel-top':'')}>
  <header className="account-heading"><div className="avatar">{p.avatarText}</div><div><strong>{p.name}</strong><small>{p.workspaceLabel}</small></div><button type="button" aria-label="关闭用户菜单" onClick={()=>p.onClose(true)}>×</button></header>
  <button type="button" className="account-action" onClick={p.onGuide}><span aria-hidden="true">◇</span>使用指南<span aria-hidden="true">›</span></button>
  <div className="account-theme-row"><div><strong>深色模式</strong><small>{p.theme==='dark'?'深色 · 紫色重点色':'浅色 · 紫白配色'}</small></div><ThemeSwitch theme={p.theme} onToggle={p.toggleTheme}/></div>
  <div className="account-model"><label htmlFor="account-model-mode">当前使用</label><strong>{p.mode==='live'?(p.model||'模型配置加载中'):'本地规则演示'}</strong><select id="account-model-mode" aria-label="模型运行方式" value={p.mode} disabled={p.busy} onChange={e=>p.onMode(e.target.value as 'live'|'demo')}><option value="live" disabled={!p.liveAvailable}>真实模型{p.model?' · '+p.model:''}</option><option value="demo">本地规则演示 · 不调用模型</option></select>{p.busy&&<small>任务进行中，结束后可切换</small>}</div>
  <button type="button" className="account-action" onClick={p.onSettings}><span aria-hidden="true">⚙</span>模型与工具<span aria-hidden="true">›</span></button>
  <div className="account-separator"/>
  <button type="button" className="account-action account-logout" onClick={p.onLogout}>退出并切换账号</button>
 </div>;
}
