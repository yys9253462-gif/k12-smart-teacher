"""K12 Smart Teacher Web MVP.

Run locally with: uvicorn app:app --reload
The API key is accepted only for the current request and is never persisted.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "web"
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}

app = FastAPI(title="K12 Smart Teacher", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class GradeResult(BaseModel):
    subject: str
    grade: str
    overview: str
    questions: list[dict]
    weak_points: list[str]
    next_steps: list[str]
    caution: str


def system_prompt(subject: str, grade: str) -> str:
    return f"""你是一位严谨、友善的中国 K12 教师。请批改学生上传的作业。
学生年级：{grade or '未提供'}；学科：{subject or '请从题目判断'}。
只根据图片/PDF中看得到的题目和答案评分；看不清、题干残缺或教材版本会影响判断时，明确标注“需人工确认”，不要猜测。
不要只给答案。逐题说明学生答案、判定、建议分数、错因和简短易懂的讲解。
输出必须是 JSON 对象，严格符合以下结构：
{{
  "subject": "学科", "grade": "年级", "overview": "总体评价",
  "questions": [{{"number":"题号", "question":"题目摘要", "student_answer":"学生答案", "status":"正确|错误|部分正确|需人工确认", "score":"得分/满分或建议", "reason":"依据", "explanation":"面向学生的讲解", "confidence": 0.0}}],
  "weak_points": ["知识点"],
  "next_steps": ["一条可执行建议"],
  "caution": "识别或评分不确定性说明"
}}
confidence 为 0 到 1 的数字。不要编造题目、答案、分数或教材要求。"""


async def call_model(*, api_key: str, base_url: str, model: str, media: bytes, mime_type: str,
                     subject: str, grade: str, rubric: str) -> GradeResult:
    data_url = f"data:{mime_type};base64,{base64.b64encode(media).decode('ascii')}"
    user_text = "请批改这份作业。"
    if rubric.strip():
        user_text += f"\n教师补充评分规则：{rubric.strip()}"
    payload = {
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt(subject, grade)},
            {"role": "user", "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]},
        ],
    }
    url = base_url.rstrip("/") + "/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(url, headers={"Authorization": f"Bearer {api_key}"}, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        return GradeResult.model_validate(json.loads(content))
    except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail="模型调用或返回格式失败。请检查 Base URL、模型是否支持视觉输入，以及 API Key。") from exc


@app.get("/")
async def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "api_key_storage": "disabled"}


@app.post("/api/grade", response_model=GradeResult)
async def grade_homework(
    file: UploadFile = File(...),
    api_key: str = Form(..., min_length=8),
    base_url: str = Form("https://api.openai.com/v1"),
    model: str = Form("gpt-4.1-mini"),
    subject: str = Form(""),
    grade: str = Form(""),
    rubric: str = Form(""),
) -> GradeResult:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="仅支持 JPG、PNG、WEBP 或 PDF 文件。")
    media = await file.read()
    if not media or len(media) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="文件不能为空且不得超过 12MB。")
    # Some providers do not accept PDF as image_url. Convert it before production use.
    if file.content_type == "application/pdf":
        raise HTTPException(status_code=422, detail="当前 MVP 请上传清晰的单页图片；PDF 转图片支持将在下一阶段加入。")
    return await call_model(api_key=api_key, base_url=base_url, model=model, media=media,
                            mime_type=file.content_type, subject=subject, grade=grade, rubric=rubric)

