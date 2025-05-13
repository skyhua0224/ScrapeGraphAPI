import os
from typing import Dict, Any, Optional, Union
from scrapegraphai.graphs import SmartScraperGraph
# from scrapegraphai.utils import prettify_exec_info # 可选，如果需要详细执行信息

# 注意：默认 Prompt 已根据用户要求移除。API 调用者必须提供 Prompt。

def scrape_url(
    prompt: str, # Prompt 现在是必需的，由调用方提供
    source_url: str,
    llm_config: Dict[str, Any],
    embedding_config: Dict[str, Any],
    verbose: bool = False,
    headless: bool = True
) -> Optional[Union[Dict, list]]:
    """
    使用 ScrapeGraphAI 从单个 URL 提取信息。

    Args:
        prompt: 用于指导提取的提示 (必需)。
        source_url: 要抓取的 URL。
        llm_config: ScrapeGraphAI 的 LLM 配置字典。
        embedding_config: ScrapeGraphAI 的 Embedding 配置字典。
        verbose: 是否打印详细执行信息。
        headless: 是否以无头模式运行浏览器。

    Returns:
        提取结果 (字典或列表)，如果发生错误则返回 None。
    """
    print(f"\n--- [Scraper] 正在处理 URL: {source_url} ---")

    # 动态构建图配置
    graph_config = {
        "llm": llm_config,
        "embeddings": embedding_config,
        "verbose": verbose,
        "headless": headless,
    }

    # 创建 SmartScraperGraph 实例
    smart_scraper_graph = SmartScraperGraph(
        prompt=prompt,
        source=source_url,
        config=graph_config
    )

    try:
        result = smart_scraper_graph.run()
        print(f"--- [Scraper] URL: {source_url} 处理完成 ---")
        # print("\n--- 提取结果 ---")
        # print(result) # 不在此处打印完整结果，由调用方处理

        # 可选：获取并打印详细执行信息
        # if verbose:
        #     exec_info = smart_scraper_graph.get_execution_info()
        #     print("\n--- 执行信息 ---")
        #     # print(prettify_exec_info(exec_info)) # 取消注释以打印

        return result

    except Exception as e:
        print(f"\n--- [Scraper] 处理 URL {source_url} 时发生错误: {e} ---")
        # 在这里可以添加更详细的错误日志记录
        return None

# 如果直接运行此脚本，可以添加一些测试代码
if __name__ == '__main__':
    # 这是一个示例，需要设置环境变量才能运行
    print("这是一个 Scraper 模块，请通过 API 服务调用。")
    # test_llm_config = {
    #     "model": "gemini-1.5-flash-latest",
    #     "api_key": os.getenv("GEMINI_API_KEY"),
    #     "temperature": 0,
    # }
    # test_embedding_config = {
    #     "model": "models/embedding-001",
    #     "api_key": os.getenv("GEMINI_API_KEY"),
    #     "type": "google"
    # }
    # test_url = "https://movie.douban.com/subject/1292052/awards/" # 示例 URL
    #
    # if test_llm_config["api_key"] and test_embedding_config["api_key"]:
    #     print(f"测试抓取 URL: {test_url}")
    #     # 测试时需要提供一个 prompt
    #     test_prompt = "请提取页面标题"
    #     scrape_result = scrape_url(
    #         prompt=test_prompt,
    #         source_url=test_url,
    #         llm_config=test_llm_config,
    #         embedding_config=test_embedding_config,
    #         verbose=True
    #     )
    #     if scrape_result:
    #         print("\n--- 测试抓取结果 ---")
    #         print(scrape_result)
    #     else:
    #         print("测试抓取失败。")
    # else:
    #     print("请设置 GEMINI_API_KEY 环境变量以运行测试。")