# K12 作业批改工具

一个本地运行的 K12 作业图片批改 Web 应用。上传作业照片后，应用通过你自行配置的、兼容 OpenAI API 的视觉模型生成逐题批改结果。

本项目**只通过 API Key 调用模型**：不需要安装或接入任何智能体、Skill、Agent 平台、记忆系统或联网搜索工具。

## 功能

- 上传 JPG、PNG、WEBP 格式的清晰作业照片（最大 12MB）
- 每次批改时填写 API Key、API Base URL 与视觉模型名称
- 支持 OpenAI-compatible 接口，例如 OpenAI、DeepSeek、通义兼容接口、OneAPI、硅基流动或本地 Ollama 服务（前提是模型支持图片输入与 Chat Completions）
- 可选填写学生年级、学科和教师评分要求
- 输出逐题状态、建议得分、批改依据、讲解、置信度、薄弱知识点与后续建议
- 对模型不确定的识别结果提示人工复核

## API Key 与隐私

- API Key 仅在当前浏览器请求中提交给本地服务，用于转发到你指定的模型供应商。
- 应用不会将 API Key 写入文件、数据库、日志或浏览器存储。
- 应用不会保存作业图片和批改记录；刷新页面后结果即丢失。
- 作业图片会发送给你填入的 API Base URL 对应服务。请在使用前确认该服务的数据处理政策，并在涉及未成年人作业时取得必要授权。

## 本地运行

要求：Python 3.10 或更高版本。

```bash
git clone https://github.com/yys9253462-gif/k12-smart-teacher.git
cd k12-smart-teacher

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app:app --reload
```

浏览器打开 <http://127.0.0.1:8000>。

## 使用方式

1. 选择一张清晰、完整、单页的作业图片。
2. 输入你的 API Key。
3. 填写接口地址和支持视觉输入的模型名；OpenAI 默认值为 `https://api.openai.com/v1` 与 `gpt-4.1-mini`。
4. 可按需补充学科、年级和评分规则。
5. 点击“开始批改”，再人工检查低置信度或“需人工确认”的题目。

## 接口要求

服务端调用：

```text
POST {Base URL}/chat/completions
Authorization: Bearer {API Key}
```

请求内容遵循 OpenAI Chat Completions 的图片输入格式，因此所选服务和模型必须同时支持该接口与视觉输入。

## 当前限制

- 当前仅支持单张图片，不支持 PDF、多页作业和摄像头拍摄。
- 不提供账户、班级管理、学生档案、批改历史、成绩发布或自动通知。
- 不会自动联网搜索资料、推荐视频或执行外部操作。
- 模型输出只能作为辅助批改，不应用作未经教师/家长复核的正式成绩。

## 项目结构

```text
app.py                    # FastAPI 后端与 OpenAI-compatible API 调用
web/                      # 静态网页前端
requirements.txt          # 运行依赖
scripts/generate_paper.py # 独立的练习卷文件生成脚本
```

## 开发验证

```bash
python -m py_compile app.py
```

## 许可证

[MIT](LICENSE)
