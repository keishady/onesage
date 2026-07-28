# OneSage v0.1.0-alpha Release Ready

该目录是公开发布副本，包名与公开代码结构已统一为 OneSage / onesage。

## 当前公开结构

- `onesage/`
- `onesage/cli.py`
- `onesage/core/`
- `onesage/data/`
- `onesage/prompts/`
- `onesage/strategic/`
- `docs/`
- `pyproject.toml`
- `README.md`
- `CONTRIBUTING.md`

## CLI 验证命令

```bash
python -m onesage.cli --help
python -m onesage.cli strategize "我要不要继续做 YouTube 频道？"
```

## 发布注意

- 公开包名：`onesage`
- 公开品牌名：`OneSage`
- CLI 入口：`onesage = "onesage.cli:main"`
- 发布目录不保留旧包名、旧品牌名或旧路径引用。