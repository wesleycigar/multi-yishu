# 木雷易术引擎 · 云端免费版（核心全功能 · 古籍检索降级）
FROM python:3.12-slim

WORKDIR /app

# 先装依赖，利于 Docker 层缓存
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制核心引擎代码（不含大索引/古籍，见 .dockerignore）
COPY *.py ./

# DeepSeek 密钥通过环境变量注入，绝不写入镜像
ENV PYTHONUNBUFFERED=1
ENV DEEPSEEK_API_KEY=""

EXPOSE 8000

# 单 worker + 多线程：512MB 免费实例内存友好
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "1", "--threads", "2", "--timeout", "120", "web_app:app"]
