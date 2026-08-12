#!/usr/bin/env python3
# weibo_publish.py —— 加载器包装器（2026-08-04 重建）
#
# 背景：原始 scripts/weibo_publish.py 源文件已丢失，仓库仅剩
# scripts/__pycache__/weibo_publish.cpython-313.pyc（2026-07-24 编译）。
# 本文件负责从 .pyc 直接加载并执行，使原本的调用方式
#   python3 scripts/weibo_publish.py publish --limit 2
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

# 加载并执行主模块 weibo_publish（__name__ 设为 __main__ 触发主流程）
# 转发命令行参数（publish / login / --limit 等）
MAIN_PYC = os.path.join(PYCDIR, "weibo_publish.cpython-313.pyc")
main_loader = PycLoader("__main__", MAIN_PYC)
main_spec = importlib.util.spec_from_file_location(
    "__main__", MAIN_PYC, loader=main_loader
)
main_mod = importlib.util.module_from_spec(main_spec)
main_mod.__file__ = os.path.join(SCRIPTS, "weibo_publish.py")
sys.modules["__main__"] = main_mod
main_spec.loader.exec_module(main_mod)
