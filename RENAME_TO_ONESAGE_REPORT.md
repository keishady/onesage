# OneSage Rename Report

## 1. 修改文件列表

- `.gitignore`
- `CONTRIBUTING.md`
- `README.md`
- `RELEASE_READY.md`
- `pyproject.toml`
- `docs/ARCHITECTURE.md`
- `docs/BRANDING.md`
- `docs/GitHub_File_Manifest.md`
- `docs/GitHub_PreRelease_Check.md`
- `docs/ROADMAP.md`
- `docs/Security_Audit.md`
- `onesage/__init__.py`
- `onesage/audit.py`
- `onesage/cli.py`
- `onesage/db.py`
- `onesage/execution_kernel.py`
- `onesage/growth_kernel.py`
- `onesage/method_kernel.py`
- `onesage/model_router.py`
- `onesage/objection_kernel.py`
- `onesage/safety.py`
- `onesage/schemas.py`
- `onesage/semantic_analyzer.py`
- `onesage/workspace.py`
- `onesage/core/__init__.py`
- `onesage/core/onesage64gua.py`
- `onesage/data/onesage64gua.jsonl`
- `onesage/prompts/METHOD.md`
- `onesage/prompts/SOUL.md`
- `onesage/strategic/__init__.py`
- `onesage/strategic/advisor.py`
- `onesage/strategic/calibration.py`
- `onesage/strategic/commitment.py`
- `onesage/strategic/confidence.py`
- `onesage/strategic/context.py`
- `onesage/strategic/contradiction.py`
- `onesage/strategic/memory.py`
- `onesage/strategic/pattern_memory.py`
- `onesage/strategic/pattern_retrieval.py`
- `onesage/strategic/patterns.py`
- `onesage/strategic/pipeline.py`
- `onesage/strategic/retrieval.py`
- `onesage/strategic/risk.py`
- `onesage/strategic/schemas.py`
- `onesage/strategic/situation.py`
- `onesage/strategic/solvability.py`
- `onesage/strategic/timing.py`

## 2. 目录变化

- 顶层 Python 包目录已改为 `onesage/`。
- CLI 文件现在位于 `onesage/cli.py`。
- core 模块现在位于 `onesage/core/`。
- data 文件现在位于 `onesage/data/`。
- prompts 文件现在位于 `onesage/prompts/`。
- strategic 模块现在位于 `onesage/strategic/`。
- 64 gua 模块文件已改为 `onesage/core/onesage64gua.py`。
- 64 gua 数据文件已改为 `onesage/data/onesage64gua.jsonl`。

## 3. 替换数量

- Title-case 旧品牌名文本替换：29
- Lowercase 旧包名/路径文本替换：85
- Uppercase 旧环境变量前缀文本替换：1
- 文本替换合计：115
- 路径重命名：3

## 4. 测试结果

- `python -m onesage.cli --help`：通过。CLI 显示程序名为 `onesage`，入口正常。
- `python -m onesage.cli strategize "我要不要继续做 YouTube 频道？"`：通过。strategic 模块正常输出 `OneSage Strategic Judgment`，结论为 `B_small_test`。
- `python -m py_compile onesage\cli.py onesage\core\onesage64gua.py onesage\workspace.py`：通过。

## 5. 残留扫描结果

- 公开工作树内容扫描：0 处旧名残留。
- 公开工作树路径扫描：0 处旧名残留。
- 测试产生的 `__pycache__` 目录已清理。

## 6. 执行边界

- 仅修改发布目录。
- 源目录只读参考，未修改。
- 未执行 commit、push 或其他远端发布操作。
