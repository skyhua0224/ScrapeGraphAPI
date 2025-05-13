# 使用官方 Python 运行时作为父镜像
# 选择 slim 版本以减小镜像体积
FROM docker.1ms.run/python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖 (如果需要，例如某些库可能需要 build-essential 或其他包)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#  && rm -rf /var/lib/apt/lists/*

# 将依赖文件复制到工作目录
COPY requirements.txt ./

# 安装项目依赖
# --no-cache-dir: 不存储缓存，减小镜像大小
# --compile: 预编译 pyc 文件，可能略微加快启动速度
RUN pip install --no-cache-dir --compile -r requirements.txt

# 下载 Playwright 浏览器二进制文件并尝试安装系统依赖 (scrapegraphai 需要)
# --with-deps 会使用 apt-get (或其他包管理器) 来安装缺失的库
RUN apt-get update && apt-get install -y --no-install-recommends sudo # --with-deps 可能需要 sudo
RUN playwright install --with-deps chromium # 安装 chromium 并包含系统依赖
RUN apt-get clean && rm -rf /var/lib/apt/lists/* # 清理 apt 缓存

# 将项目代码复制到工作目录
# 注意：使用 .dockerignore 文件来排除不需要复制的文件 (如 .git, .env, etc.)
COPY . .

# 暴露 FastAPI 应用监听的端口
EXPOSE 8000

# 定义容器启动时运行的命令
# 使用 uvicorn 运行 FastAPI 应用
# --host 0.0.0.0 使其可以从容器外部访问
# --port 8000 监听的端口
# api:app 指向 api.py 文件中的 app = FastAPI() 实例
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

# 对于生产环境，可以考虑不使用 reload，并可能增加 workers 数量
# CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]