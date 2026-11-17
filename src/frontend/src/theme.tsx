import {useState} from 'react';
type Theme='dark'|'light';
const KEY='a4g-theme';
function initial():Theme {try {return localStorage.getItem(KEY)==='light'?'light':'dark';}catch{return 'dark';}}
const first=initial();document.documentElement.dataset.theme=first;
export function useTheme():[Theme,()=>void]{
 const [theme,setTheme]=useState<Theme>(first);
 const toggle=()=>setTheme(current=>{const next=current==='dark'?'light':'dark';document.documentElement.dataset.theme=next;try{localStorage.setItem(KEY,next);}catch{/* Storage may be unavailable; switching still works. */}return next;});
 return [theme,toggle];
}
export function ThemeToggle({theme,onToggle}:{theme:Theme;onToggle:()=>void}){
 const label=theme==='dark'?'切换到浅色模式':'切换到深色模式';
 return <button type="button" className="theme-toggle" aria-label={label} title={label} onClick={onToggle}>
 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">{theme==='dark'?<><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></>:<path d="M20.5 13.5A9 9 0 0 1 10.5 3.4a9 9 0 1 0 10 10.1Z"/>}</svg><span>{theme==='dark'?'浅色':'深色'}</span></button>;
}

export function ThemeSwitch({theme,onToggle}:{theme:Theme;onToggle:()=>void}){
 return <button type="button" role="switch" aria-checked={theme==='dark'} aria-label="深色模式" className="theme-switch" onClick={onToggle}><span aria-hidden="true"/></button>;
}
