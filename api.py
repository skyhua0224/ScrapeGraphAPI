import os
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, HttpUrl, Field, model_validator
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# 导入重构后的抓取函数
from scraper import scrape_url # 移除 DEFAULT_PROMPT 的导入

# 加载 .env 文件中的环境变量 (主要用于本地开发)
# 在 Docker Compose 中，环境变量通常由 compose 文件注入
load_dotenv()

# --- 配置读取与验证 ---

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434") # Docker Compose 服务名
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
GOOGLE_EMBEDDING_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/embedding-001")

SCRAPEGRAPHAI_VERBOSE = os.getenv("SCRAPEGRAPHAI_VERBOSE", "False").lower() == "true"
SCRAPEGRAPHAI_HEADLESS = os.getenv("SCRAPEGRAPHAI_HEADLESS", "True").lower() == "true"

# 启动时检查关键配置
if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY:
    raise ValueError("LLM_PROVIDER is 'gemini' but GEMINI_API_KEY is not set.")
if LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY:
    raise ValueError("LLM_PROVIDER is 'deepseek' but DEEPSEEK_API_KEY is not set.")
if EMBEDDING_PROVIDER == "google" and not GEMINI_API_KEY:
    raise ValueError("EMBEDDING_PROVIDER is 'google' but GEMINI_API_KEY is not set (used for Google Embedding).")
if EMBEDDING_PROVIDER == "ollama" and not OLLAMA_BASE_URL:
     raise ValueError("EMBEDDING_PROVIDER is 'ollama' but OLLAMA_BASE_URL is not set.")

# --- FastAPI 应用定义 ---

app = FastAPI(
    title="Scraping Service API",
    description="通过 API 调用 ScrapeGraphAI 进行网页信息提取",
    version="0.1.0",
)

# --- Pydantic 模型定义 ---

class ScrapeRequest(BaseModel):
    urls_input: str = Field(..., alias="urls", description="需要抓取的 URL 列表，每行一个 URL")
    prompt: str = Field(..., description="指导信息提取的 Prompt (必需)") # 移除默认值，使其成为必需字段
    parsed_urls: List[HttpUrl] = Field(default_factory=list, exclude=True) # 用于存储解析后的URL

    @model_validator(mode='after')
    def parse_urls_from_input(self) -> 'ScrapeRequest':
        if isinstance(self.urls_input, str):
            url_strings = self.urls_input.splitlines()
            validated_urls = []
            for i, url_str in enumerate(url_strings):
                url_str = url_str.strip()
                if not url_str: # 跳过空行
                    continue
                try:
                    validated_urls.append(HttpUrl(url_str))
                except ValueError as e:
                    # 提供更详细的错误信息，指出是哪个URL以及具体错误
                    raise ValueError(f"第 {i+1} 个 URL '{url_str}' 无效: {e}")
            self.parsed_urls = validated_urls
        elif isinstance(self.urls_input, list): # 兼容已经传递列表的情况 (虽然主要场景是字符串)
            # 如果已经是 HttpUrl 列表，直接使用
            if all(isinstance(u, HttpUrl) for u in self.urls_input):
                self.parsed_urls = self.urls_input
            else: # 如果是字符串列表，尝试转换
                validated_urls = []
                for i, url_str in enumerate(self.urls_input):
                    url_str = str(url_str).strip()
                    if not url_str:
                        continue
                    try:
                        validated_urls.append(HttpUrl(url_str))
                    except ValueError as e:
                        raise ValueError(f"URL 列表中第 {i+1} 个 URL '{url_str}' 无效: {e}")
                self.parsed_urls = validated_urls
        else:
            raise ValueError("urls 必须是字符串 (每行一个URL) 或有效的URL列表")

        if not self.parsed_urls:
            raise ValueError("至少需要提供一个有效的 URL。")
        return self

class ScrapeResponseItem(BaseModel):
    url: HttpUrl
    status: str # "success" or "error"
    data: Optional[Any] = None # 抓取到的数据
    error_message: Optional[str] = None # 错误信息

class ScrapeResponse(BaseModel):
    results: List[ScrapeResponseItem]

# --- API 端点 ---

@app.post("/scrape", response_model=ScrapeResponse, tags=["Scraping"])
async def run_scraping(request: ScrapeRequest = Body(...)):
    """
    接收 URL 列表和 Prompt，执行抓取任务并返回结果。
    """
    results: List[ScrapeResponseItem] = []
    llm_config = {}
    embedding_config = {}

    # 1. 构建 LLM 配置
    if LLM_PROVIDER == "gemini":
        if not GEMINI_API_KEY: # 再次检查以防万一
             raise HTTPException(status_code=503, detail="Gemini API Key not configured on server.")
        llm_config = {
            "model": "gemini-1.5-flash-latest", # 或者从环境变量读取模型名称
            "api_key": GEMINI_API_KEY,
            "temperature": 0, # 或者从环境变量读取
        }
    elif LLM_PROVIDER == "deepseek":
        if not DEEPSEEK_API_KEY:
             raise HTTPException(status_code=503, detail="DeepSeek API Key not configured on server.")
        llm_config = {
            "model": "deepseek-chat", # 或者从环境变量读取模型名称
            "api_key": DEEPSEEK_API_KEY,
            "temperature": 0, # 或者从环境变量读取
            # "llm_type": "deepseek" # ScrapeGraphAI 可能需要这个，待测试确认
        }
    else:
        raise HTTPException(status_code=500, detail=f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")

    # 2. 构建 Embedding 配置
    if EMBEDDING_PROVIDER == "google":
        if not GEMINI_API_KEY:
             raise HTTPException(status_code=503, detail="Gemini API Key (for Google Embeddings) not configured.")
        embedding_config = {
            "model": GOOGLE_EMBEDDING_MODEL,
            "api_key": GEMINI_API_KEY,
            "type": "google"
        }
    elif EMBEDDING_PROVIDER == "ollama":
        # 注意：这里的配置格式需要根据 ScrapeGraphAI 对 Ollama Embedding 的实际支持情况调整
        # 可能的格式包括直接传递 base_url 和 model，或者需要指定 type="ollama"
        embedding_config = {
            "type": "ollama", # 假设需要指定类型
            "model": OLLAMA_EMBEDDING_MODEL,
            "base_url": OLLAMA_BASE_URL # 传递 Ollama 服务地址
            # "api_key": None # Ollama 通常不需要 API Key
        }
        # 可以在这里添加检查 Ollama 服务是否可达的逻辑 (可选)
        # import ollama
        # try:
        #     ollama.Client(host=OLLAMA_BASE_URL).list()
        # except Exception as e:
        #     raise HTTPException(status_code=503, detail=f"Ollama service at {OLLAMA_BASE_URL} is unreachable: {e}")
    else:
        raise HTTPException(status_code=500, detail=f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")

    # 3. 遍历 URL 并执行抓取
    for url in request.parsed_urls: # 修改为使用解析后的 parsed_urls
        scrape_result = await scrape_url_async( # 使用异步包装器
            prompt=request.prompt,
            source_url=str(url), # HttpUrl 对象需要转为 str
            llm_config=llm_config,
            embedding_config=embedding_config,
            verbose=SCRAPEGRAPHAI_VERBOSE,
            headless=SCRAPEGRAPHAI_HEADLESS
        )

        if scrape_result is not None:
            results.append(ScrapeResponseItem(url=url, status="success", data=scrape_result))
        else:
            results.append(ScrapeResponseItem(url=url, status="error", error_message="Scraping failed for this URL."))

    return ScrapeResponse(results=results)

# --- 异步包装器 (因为 scrape_url 是同步的) ---
# FastAPI 在事件循环中运行，直接调用阻塞的同步函数会阻塞整个服务
# 使用 run_in_threadpool 可以将同步函数放到线程池中执行，避免阻塞
from fastapi.concurrency import run_in_threadpool

async def scrape_url_async(*args, **kwargs):
    return await run_in_threadpool(scrape_url, *args, **kwargs)


# --- 本地运行服务器 ---
if __name__ == "__main__":
    print("--- Starting FastAPI Server ---")
    print(f"LLM Provider: {LLM_PROVIDER}")
    print(f"Embedding Provider: {EMBEDDING_PROVIDER}")
    if EMBEDDING_PROVIDER == 'ollama':
        print(f"Ollama URL: {OLLAMA_BASE_URL}")
        print(f"Ollama Embedding Model: {OLLAMA_EMBEDDING_MODEL}")
    print("-----------------------------")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) # reload=True 用于本地开发