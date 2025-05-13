# ScrapeGraphAPI

这是一个使用 ScrapeGraphAI 和 FastAPI 构建的 Web Scraping API 服务。它允许用户通过 API 提交 URL 列表和一个自定义的 Prompt，然后利用大型语言模型 (LLM) 和 Embedding 模型从这些网页中提取所需信息。

## 功能特性

- **基于 API 的抓取**: 通过简单的 POST 请求即可触发网页抓取任务。
- **自定义提取逻辑**: 用户可以通过提供 Prompt 来精确指导信息提取过程。
- **灵活的 LLM 支持**: 支持配置使用不同的 LLM 提供商 (当前支持 Gemini 和 DeepSeek)。
- **灵活的 Embedding 支持**: 支持配置使用不同的 Embedding 提供商 (当前支持 Google Gemini 和本地 Ollama)。
- **容器化部署**: 使用 Docker 和 Docker Compose 轻松部署和管理服务。
- **异步处理**: API 使用 FastAPI 的异步特性和线程池来处理抓取请求，避免阻塞。

## 技术栈

- **后端框架**: FastAPI
- **Web 服务器**: Uvicorn
- **核心抓取库**: ScrapeGraphAI
- **浏览器自动化**: Playwright (由 ScrapeGraphAI 使用)
- **编程语言**: Python 3.11
- **容器化**: Docker, Docker Compose
- **LLM/Embedding**: Google Gemini API, DeepSeek API, Ollama

## 安装与设置

本项目推荐使用 Docker Compose 进行部署。

1.  **克隆仓库**:

    ```bash
    git clone <your-repo-url>
    cd ScrapeGraphAPI
    ```

2.  **创建并配置 `.env` 文件**:
    复制或重命名项目根目录下的 `.env.example` (如果存在) 为 `.env`，或者手动创建 `.env` 文件。根据您的需求填入以下环境变量：

    ```dotenv
    # --- LLM Configuration ---
    # 指定 LLM 提供商: "gemini" 或 "deepseek"
    LLM_PROVIDER=deepseek
    # 如果 LLM_PROVIDER="gemini", 需要提供 Google Gemini API Key
    GEMINI_API_KEY=YOUR_GEMINI_API_KEY
    # 如果 LLM_PROVIDER="deepseek", 需要提供 DeepSeek API Key
    DEEPSEEK_API_KEY=YOUR_DEEPSEEK_API_KEY

    # --- Embedding Configuration ---
    # 指定 Embedding 提供商: "google" 或 "ollama"
    EMBEDDING_PROVIDER=ollama
    # 如果 EMBEDDING_PROVIDER="google", 需要提供 Google Gemini API Key (与 LLM 共用)
    # GEMINI_API_KEY=YOUR_GEMINI_API_KEY (如果上面已填，这里无需重复)
    # Google Embedding 模型名称 (可选, 有默认值)
    GOOGLE_EMBEDDING_MODEL=models/embedding-001
    # 如果 EMBEDDING_PROVIDER="ollama", 需要指定 Ollama 服务地址和模型
    # Docker Compose 默认的服务名是 ollama, 地址是 http://ollama:11434
    OLLAMA_BASE_URL=http://ollama:11434
    # Ollama Embedding 模型名称 (需要预先在 Ollama 中拉取, 例如 nomic-embed-text)
    OLLAMA_EMBEDDING_MODEL=nomic-embed-text

    # --- ScrapeGraphAI Configuration ---
    # 是否打印 ScrapeGraphAI 的详细日志 (true/false)
    SCRAPEGRAPHAI_VERBOSE=False
    # 是否以无头模式运行 Playwright 浏览器 (true/false)
    SCRAPEGRAPHAI_HEADLESS=True
    ```

    **重要**:

    - 确保根据您选择的 `LLM_PROVIDER` 和 `EMBEDDING_PROVIDER` 提供了对应的 API 密钥或配置。
    - 如果使用 Ollama (`EMBEDDING_PROVIDER=ollama`)，您需要在 Ollama 服务中预先拉取所需的 Embedding 模型 (例如 `ollama pull nomic-embed-text`)。Docker Compose 会启动 Ollama 服务，但不会自动拉取模型。

3.  **构建并启动服务**:
    ```bash
    docker-compose up --build -d
    ```
    - `--build` 选项会强制重新构建镜像。首次运行时需要。
    - `-d` 选项会在后台运行容器。

## API 使用

服务启动后，可以通过向 `/scrape` 端点发送 POST 请求来使用 API。

- **URL**: `http://localhost:8000/scrape` (如果通过 Docker Compose 部署)
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body** (JSON):

  ```json
  {
    "urls": ["https://example.com/page1", "https://anothersite.org/article"],
    "prompt": "请提取每个页面的主标题和所有段落的文本。"
  }
  ```

  - `urls`: 一个包含要抓取的 URL 字符串的列表。
  - `prompt`: 一个字符串，用于指导 ScrapeGraphAI 如何提取信息。**这是必需字段**。

- **示例 `curl` 请求**:

  ```bash
  curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://news.ycombinator.com/"],
    "prompt": "List the titles and URLs of the top 5 stories."
  }'
  ```

- **响应体** (JSON):
  ```json
  {
    "results": [
      {
        "url": "https://news.ycombinator.com/",
        "status": "success", // "success" 或 "error"
        "data": {
          // 提取的数据，结构取决于您的 Prompt
          "top_stories": [
            { "title": "Story 1 Title", "url": "http://..." },
            { "title": "Story 2 Title", "url": "http://..." }
            // ...
          ]
        },
        "error_message": null // 如果 status 是 "error"，这里会有错误信息
      }
      // ... 其他 URL 的结果
    ]
  }
  ```

## 本地开发

有两种主要方式进行本地开发：

1.  **直接运行 Python (不推荐用于完整测试)**:

    - 确保已安装 Python 3.11+ 和 pip。
    - 创建虚拟环境: `python -m venv venv && source venv/bin/activate` (或 `venv\Scripts\activate` on Windows)。
    - 安装依赖: `pip install -r requirements.txt`。
    - 安装 Playwright 依赖: `playwright install --with-deps chromium`。
    - 设置环境变量 (可以直接在终端设置，或者使用 `.env` 文件配合 `python-dotenv`，代码中已包含 `load_dotenv()`)。
    - 运行 API 服务: `uvicorn api:app --reload --port 8000`。
    - **注意**: 这种方式无法直接利用 Docker Compose 中的 Ollama 服务。如果需要测试 Ollama，需要单独运行 Ollama。

2.  **使用 Docker Compose (推荐)**:
    - 确保已安装 Docker 和 Docker Compose。
    - 按照 "安装与设置" 部分配置好 `.env` 文件。
    - 启动服务: `docker-compose up --build`。
    - [`docker-compose.yml`](docker-compose.yml:0) 文件中配置了卷挂载 (`.:/app`)，并且 Uvicorn 在本地运行时默认开启了 `--reload` ([`api.py`](api.py:157))。这意味着您在本地修改代码后，FastAPI 服务会自动重新加载，无需重启容器。

## Docker 部署

对于生产环境或稳定部署：

1.  确保已配置好 `.env` 文件，包含生产环境所需的 API 密钥和设置。**强烈建议不要将包含敏感密钥的 `.env` 文件直接提交到版本控制系统。** 考虑使用 Docker Secrets 或其他安全的密钥管理方式。
2.  构建并启动服务:

    ```bash
    docker-compose up --build -d
    ```

    - 移除 `--build` 如果镜像没有变化。
    - `-d` 使容器在后台运行。

3.  查看日志:

    ```bash
    docker-compose logs -f app # 查看 app 服务的日志
    docker-compose logs -f ollama # 查看 ollama 服务的日志
    ```

4.  停止服务:
    ```bash
    docker-compose down
    ```
    - 添加 `-v` 选项 (`docker-compose down -v`) 可以同时删除 `ollama_data` 卷，这将清除已下载的 Ollama 模型。

## 注意事项

- **API 密钥管理**: `.env` 文件方便本地开发，但在生产环境中请使用更安全的方式管理 API 密钥。
- **Ollama 模型**: 如果使用 Ollama，确保在启动容器前或启动后，通过 Ollama CLI 或 API 拉取所需的 Embedding 模型。
- **资源消耗**: 运行 LLM 和 Web Scraping 可能需要较多计算资源 (CPU, RAM)。根据需要调整 Docker 资源限制。
- **错误处理**: API 和 Scraper 包含基本的错误处理，但可以根据具体需求进行扩展。
