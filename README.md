# Dressing

本地优先的私人穿搭助手。Profile、衣柜和配置保存在代码仓库之外的文件目录中；应用每次请求重新读取当前文件，再通过本机 Codex CLI 生成穿搭建议。

## 当前能力

- Streamlit 聊天式穿搭助手
- 外部文件保存个人资料与衣柜
- Profile 核心摘要按需进入模型上下文，详细外貌数据仅在相关请求中读取
- 衣柜按名称保守推断品类、材质、厚薄、季节、场景与风格
- 输出 1–3 套穿搭方案和搭配理由
- 支持在第二轮对话中临时排除“正在清洗/不能穿”的衣物并重新推荐
- 支持聊天生成衣柜新增、修改、删除草案
- 只有点击“确认写入”后才会修改 `wardrobe.yaml`，写入前自动备份
- 不长期保存聊天历史，只保留当前会话最近几轮和短摘要
- 使用本机 `codex exec`，复用 CC Switch / Codex 当前模型配置
- Codex 调用使用临时会话和只读沙箱

## 技术结构

```text
app.py                         # Streamlit 入口
dressing_assistant/
├── config.py                  # 数据目录和运行配置
├── llm.py                     # Codex CLI Provider
├── models.py                  # Pydantic 数据结构
├── profile.py                 # Profile 核心摘要与按需细节
├── prompting.py               # 模型提示词
├── service.py                 # 单轮对话与文件操作编排
├── storage.py                 # YAML/Markdown、原子写入、备份
└── wardrobe.py                # 衣柜归一化与增删改
tests/                         # 自动化测试
```

## 数据目录

默认位置：

```text
~/Documents/WardrobeAssistantData/
├── profile.md
├── wardrobe.yaml
├── config.yaml
└── backups/
```

可以通过环境变量覆盖：

```bash
export DRESSING_DATA_DIR="/path/to/private/data"
```

数据目录不在 Git 仓库内。应用不会把 Profile 或衣柜数据写入代码仓库、测试文件或日志。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## 启动

```bash
./run.sh
```

`run.sh` 会在缺少 `.venv` 或依赖时自动创建和安装，然后启动 Streamlit。

浏览器打开：

```text
http://localhost:8501
```

## Codex / CC Switch 配置

`config.yaml` 默认使用：

```yaml
llm:
  provider: codex_cli
  codex_binary: /Applications/ChatGPT.app/Contents/Resources/codex
  model: null
  timeout_seconds: 180
context:
  max_recent_messages: 6
```

`model: null` 表示使用该 Codex 配置的默认模型。为了不继承 CC Switch 的 DeepSeek 配置，可以在外部 `config.yaml` 设置独立的 `codex_home`：

```yaml
llm:
  provider: codex_cli
  codex_binary: /Applications/ChatGPT.app/Contents/Resources/codex
  codex_home: /Users/your-name/Documents/WardrobeAssistantData/codex-home
  profile: null
  model: null
  timeout_seconds: 180
```

然后只对这个专用目录执行 ChatGPT 登录：

```bash
CODEX_HOME="/Users/your-name/Documents/WardrobeAssistantData/codex-home" \
/Applications/ChatGPT.app/Contents/Resources/codex login --device-auth
```

该目录与 CC Switch 使用的 `~/.codex` 分离。登录 ChatGPT 后，Dressing 会使用 Codex 默认的 GPT 模型；不需要 OpenAI API Key。

## 检查实际模型

运行：

```bash
.venv/bin/python scripts/check_model.py
```

该脚本使用与 Dressing 完全相同的 `CODEX_HOME` 和模型配置，并检查：

- 当前登录方式是否为 ChatGPT
- `provider` 是否为 `openai`
- 实际 `model` 是否为 GPT
- 最小请求能否成功

## 数据编辑

- 可以直接编辑 `profile.md` 和 `wardrobe.yaml`，下一次请求会自动读取最新文件。
- 也可以在 Streamlit 的“个人资料”和“衣柜管理”页中编辑。
- 所有通过应用写回文件的操作都会先在 `backups/` 中创建备份。
- `wardrobe.yaml` 中每项都可以使用 `inference_status: inferred` 或 `confirmed` 标记数据可信度。

## 测试

```bash
.venv/bin/python -m pytest
```

## 本地文件与 GitHub

详细说明见 [`docs/LOCAL_FILES.md`](docs/LOCAL_FILES.md)。

- 源码、测试、文档和配置模板放在 GitHub。
- `.venv` 约 381 MB，属于本机生成文件，不应上传 GitHub；删除后运行 `./run.sh` 会自动重建。
- `profile.md`、`wardrobe.yaml` 和 ChatGPT 登录状态保存在私有数据目录，不进入 GitHub。

## 隐私边界

- 普通推荐只发送 Profile 的核心穿搭摘要，不发送完整脸部细节。
- 当问题涉及脸型、肤色、配色、领口、配饰、外貌时，才会读取详细 Profile。
- 衣柜只发送紧凑字段，不发送本地文件内容之外的额外个人信息。
- 聊天历史不落盘。
- 临时排除条件不会写入衣柜文件。
- 使用独立 `CODEX_HOME` 时，Profile 和衣柜仍然只保存在本地数据目录；模型请求会发送精简穿搭上下文到所登录的 ChatGPT/Codex 服务。

## 当前限制

- 暂不自动获取天气，需要在对话中提供温度和体感。
- 暂不直接记录清洗状态，只在当前对话中临时排除。
- 暂不处理图片，衣物信息通过文字或 YAML 录入。
- 暂不提供 HTTP API。服务层已与 Streamlit 分离，后续可以增加 FastAPI 入口。
- 暂不使用 SQLite；对于当前个人衣柜规模，文件加载和重建上下文足够快。
