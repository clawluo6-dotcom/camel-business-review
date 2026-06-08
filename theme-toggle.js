/* ================================================================
   theme-toggle.js — 暗色 / 纸墨书香 双主题切换
   用法：在 </body> 前引入此脚本
   ================================================================ */

(function() {
  const KEY = 'camel-theme';
  const STORED = localStorage.getItem(KEY) || 'scholar';

  // 初始化：根据 localStorage 设置 html class
  const html = document.documentElement;
  html.classList.remove('dark', 'scholar');
  html.classList.add(STORED);

  // 注入切换按钮到导航栏
  function injectToggle() {
    const navRight = document.querySelector('nav .flex.items-center.gap-8');
    if (!navRight) return;

    const btn = document.createElement('button');
    btn.className = 'theme-toggle';
    btn.title = '切换主题';
    updateButtonText(btn, STORED);

    btn.addEventListener('click', function() {
      const current = html.classList.contains('scholar') ? 'scholar' : 'dark';
      const next = current === 'dark' ? 'scholar' : 'dark';
      html.classList.remove('dark', 'scholar');
      html.classList.add(next);
      localStorage.setItem(KEY, next);
      updateButtonText(btn, next);
      // 发出主题变更事件，供 Giscus 等组件监听
      window.dispatchEvent(new CustomEvent('camel-theme-changed', { detail: next }));
    });

    navRight.appendChild(btn);
  }

  function updateButtonText(btn, theme) {
    if (theme === 'scholar') {
      btn.innerHTML = '\u{1F319}\u00A0暗色';
    } else {
      btn.innerHTML = '\u{1F4DC}\u00A0纸墨';
    }
  }

  // DOM 就绪后注入
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectToggle);
  } else {
    injectToggle();
  }
})();
