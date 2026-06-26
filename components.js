/* ================================================================
   components.js — 共享组件（导航栏、页脚、PILLAR_CONFIG）
   所有页面引入此文件替代重复的 HTML 模板
   用法：在 <body> 中放置 <div id="site-nav"></div><div id="site-footer"></div>
   并在 </body> 前引入此脚本
   ================================================================ */

window.__PILLAR_CONFIG__ = {
  worldview: {
    name: '🌌 世界观 · 哲学思想研究', slug: 'worldview.html', accent: '#22d3ee',
    subAccent: '#06b6d4', accentRgb: '34,211,238',
    pillarName: '一、传统哲学研究'
  },
  social: {
    name: '🏛️ 经济逻辑 · 经济研究', slug: 'social.html', accent: '#f59e0b',
    subAccent: '#d97706', accentRgb: '245,158,11',
    pillarName: '二、经济研究'
  },
  practice: {
    name: '🧘 思想与修行', slug: 'practice.html', accent: '#a855f7',
    subAccent: '#7c3aed', accentRgb: '168,85,247',
    pillarName: '三、思想与修行'
  }
};

(function() {
  var ACTIVE_NAV = document.documentElement.getAttribute('data-nav') || '';

  // 导航链接配置
  var NAV_LINKS = [
    { href: 'index.html', label: '首页', accent: 'accent-cyan' },
    { href: 'worldview.html', label: '🌌 世界观', accent: 'accent-cyan' },
    { href: 'social.html', label: '🏛️ 经济逻辑', accent: 'accent-gold' },
    { href: 'ai-news.html', label: '资产速报', accent: 'accent-emerald' },
    { href: 'about.html', label: '✦ 关于', accent: 'accent-purple' },
  ];

  // 平台链接配置
  var PLATFORM_LINKS = [
    { href: 'https://www.ximalaya.com/zhubo/3049357', label: '喜马拉雅', icon: '🎙️', title: '喜马拉雅' },
    { href: 'https://space.bilibili.com/527952781', label: 'B站', icon: '📺', title: 'B站' },
    { href: 'https://zhuanlan.zhihu.com/c_1033349413602889728', label: '知乎', icon: '✍️', title: '知乎' },
    { href: 'https://mp.sohu.com/profile?xpt=ODg1NDI3OTk1NDIxMjE2NzY4QHNvaHUuY29t', label: '搜狐号', icon: '📰', title: '搜狐号' },
  ];

  function renderNav() {
    var linksHtml = NAV_LINKS.map(function(l) {
      var activeClass = '';
      var style = '';
      if (ACTIVE_NAV === l.href.replace('.html', '')) {
        activeClass = ' active';
        style = ' style="color:#fbbf24"';
      }
      return '<a href="' + l.href + '" class="nav-link text-text-secondary hover:text-' + l.accent + ' transition no-underline' + activeClass + '"' + style + '>' +
             '<span>' + l.label + '</span></a>';
    }).join('');

    return '' +
    '<nav class="sticky top-0 z-50 glass border-b border-white/5">' +
      '<div class="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">' +
        '<a href="index.html" class="flex items-center gap-3 no-underline shrink-0" style="text-decoration:none">' +
          '<div class="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-purple flex items-center justify-center">' +
            '<span class="text-white font-bold text-sm">✦</span>' +
          '</div>' +
          '<div>' +
            '<h1 class="text-lg font-bold tracking-tight"><span class="gradient-text">骆驼</span>🐫 <span class="text-text-secondary font-normal">商业本质</span></h1>' +
          '</div>' +
        '</a>' +
        '<div class="flex items-center gap-8">' +
          linksHtml +
        '</div>' +
      '</div>' +
    '</nav>';
  }

  function renderFooter(showAbout) {
    var platformHtml = PLATFORM_LINKS.map(function(p) {
      return '<a href="' + p.href + '" target="_blank" rel="noopener" class="glass rounded-lg px-4 py-2.5 text-sm font-medium text-text-secondary hover:text-accent-cyan hover:border-accent-cyan/30 transition-all duration-300 no-underline inline-flex items-center gap-2" style="border:1px solid rgba(255,255,255,0.08);" title="' + (p.title || '') + '">' +
             '<span class="text-lg">' + p.icon + '</span> ' + p.label +
             '</a>';
    }).join('');

    return '' +
    '<footer class="border-t border-white/5 mt-8 bg-bg-secondary/50">' +
      '<div class="max-w-5xl mx-auto px-6 py-6">' +
        '<div class="flex flex-col md:flex-row items-center justify-between gap-5 mb-3">' +
          '<div class="flex items-center gap-3">' +
            '<span class="gradient-text font-bold text-xl">骆驼</span>🐫 <span class="gradient-text font-bold text-xl">商业本质</span>' +
            '<span class="text-text-muted text-base">·</span>' +
            '<span class="text-text-secondary text-base">个人跨领域独立研究</span>' +
          '</div>' +
          '<div class="flex items-center gap-3">' +
            platformHtml +
          '</div>' +
        '</div>' +
        '<div class="flex items-center justify-center gap-3 text-[11px] text-text-muted">' +
          '<a href="index.html" class="hover:text-accent-cyan transition">首页</a>' +
          '<span>·</span>' +
          '<a href="worldview.html" class="hover:text-accent-cyan transition">世界观</a>' +
          '<span>·</span>' +
          '<a href="social.html" class="hover:text-accent-gold transition">经济逻辑</a>' +
          '<span>·</span>' +
          '<a href="practice.html" class="hover:text-accent-purple transition">思想与修行</a>' +
          '<span>·</span>' +
          '<span class="opacity-50">&copy; 2016-2026 骆驼商业本质</span>' +
        '</div>' +
      '</div>' +
    '</footer>';
  }

  // 注入 nav
  var navEl = document.getElementById('site-nav');
  if (navEl) {
    navEl.innerHTML = renderNav();
  }

  // 注入 footer
  var footerEl = document.getElementById('site-footer');
  if (footerEl) {
    footerEl.innerHTML = renderFooter();
  }
})();
