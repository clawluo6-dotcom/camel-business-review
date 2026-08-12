#!/usr/bin/env python3
# zhihu_publish.py —— 加载器包装器（2026-08-04 重建）
#
# 背景：原始 scripts/zhihu_publish.py 源文件已丢失，仓库仅剩
# scripts/__pycache__/zhihu_publish.cpython-313.pyc（2026-07-24 编译）。
# 本文件负责从 .pyc 直接加载并执行，使原本的调用方式
#   python3 scripts/zhihu_publish.py publish --limit 2
# 继续可用。依赖 publish_common / devto_publish 的 .pyc 同样在 __pycache__ 中。
#
# 若日后从备份/远程恢复了真正的 .py 源文件，请直接覆盖本文件。
import importlib.machinery
import importlib.util
import os
import sys
import types

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "scripts")
PYCDIR = os.path.join(SCRIPTS, "__pycache__")


def _fake_py_path(name):
    return os.path.join(SCRIPTS, name + ".py")


class PycLoader(importlib.machinery.SourcelessFileLoader):
    """从 .pyc 加载，但在 exec 之前把 __file__ 伪装成 scripts/<name>.py，
    使脚本内部 dirname(__file__) / dirname(dirname(__file__)) 正确解析仓库根。"""

    def create_module(self, spec):
        module = super().create_module(spec)
        if module is None:
            module = types.ModuleType(spec.name)
        module.__file__ = _fake_py_path(spec.name)
        module.__loader__ = self
        module.__spec__ = spec
        return module


class PycMetaFinder:
    def find_spec(self, name, path=None, target=None):
        p = os.path.join(PYCDIR, name + ".cpython-313.pyc")
        if not os.path.exists(p):
            return None
        loader = PycLoader(name, p)
        return importlib.util.spec_from_file_location(name, p, loader=loader)


sys.meta_path.insert(0, PycMetaFinder())
os.chdir(REPO)

# 加载并执行主模块 zhihu_publish（__name__ 设为 __main__ 触发主流程）
# 转发命令行参数（publish / login / --limit 等）
MAIN_PYC = os.path.join(PYCDIR, "zhihu_publish.cpython-313.pyc")
main_loader = PycLoader("__main__", MAIN_PYC)
main_spec = importlib.util.spec_from_file_location(
    "__main__", MAIN_PYC, loader=main_loader
)
main_mod = importlib.util.module_from_spec(main_spec)
main_mod.__file__ = os.path.join(SCRIPTS, "zhihu_publish.py")
sys.modules["__main__"] = main_mod

# ===== 知乎专属脚注：只给「联系方式 + 网页地址出处」，去掉 devto 的营销导流话术 =====
# 仅在加载知乎主模块前覆盖 publish_common 上的 build_byline / FOOTER 两个全局，
# 知乎 build_html 通过 pc.build_byline / pc.FOOTER 访问，patch 后生效；
# devto_publish 仍用自身原 FOOTER，互不影响。
import publish_common  # 已被 PycMetaFinder 接管，从 .pyc 加载

ZH_SITE = "https://clawluo6-dotcom.github.io/camel-business-review"
ZH_AUTHOR = "骆新中"
# TODO(用户补充): 替换为你的真实知乎主页链接；暂用搜索引导避免空链接
ZH_CONTACT = "在知乎搜索「骆新中」即可关注 / 私信作者"


def _zhihu_byline(date):
    return (
        f"> ✦ **作者：{ZH_AUTHOR}**　｜　联系方式：{ZH_CONTACT}\n"
        f"> 撰写于 {date}"
    )


publish_common.build_byline = _zhihu_byline
publish_common.FOOTER = (
    "\n\n---\n\n"
    f"> 本文全文首发于 **《骆驼商业本质》**：{ZH_SITE}\n"
)

main_spec.loader.exec_module(main_mod)
