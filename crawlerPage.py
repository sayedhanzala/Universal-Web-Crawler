import asyncio
import os
import re
import csv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime

async def main(url):
    # 1. Set up browser configuration for pure text crawling
    browser_conf = BrowserConfig(
        browser_type="chromium",
        headless=True,
        viewport_width=1280,
        viewport_height=720,
        text_mode=False,  # Get HTML content
    )

    # 2. Set up crawler run configuration without LLM strategy
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
    )

    # 3. Create and run the crawler to get raw content
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url,
            config=run_conf,
        )

        if not result.success:
            print("Crawl Error:", result.error_message)
            return

        # Initialize Gemini directly through LangChain
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0,
        )

        # Extract HTML content
        markdown_content = result.markdown

        # Create a prompt for the model
        prompt = f"""
        TASK: Extract and format the main article content from this webpage.
        
        FORMAT REQUIREMENTS:
        1. INCLUDE ONLY:
        - The main article title
        - The complete article body text
        - Any relevant subheadings within the article
        - Any embedded content that's part of the main article
        
        2. FORMAT as clean markdown with:
        - Images preserved in markdown format
        - Main title with ##
        - Subheadings with #
        - Preserve original text formatting (lists, paragraphs, etc.)
        
        3. EXCLUDE:
        - Navigation elements
        - Menus and sidebars
        - Headers and footers
        - Advertisements
        - Comments sections
        - Related articles
        - Any content not part of the main article
        - Any relevant header image
        
        MARKDOWN CONTENT:
        {markdown_content}
        """

        # Process with Gemini directly
        response = model.invoke([HumanMessage(content=prompt)])

        # Print the cleaned result
        print("Extracted Markdown Content:")
        print(response.content)


# def save_links_to_csv(links, source_url, filename="extracted_links.csv"):
#     file_exists = os.path.isfile(filename)
#     fieldnames = ["timestamp", "source", "text", "url"]

#     # Add timestamp and source to each link
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     enhanced_links = []
#     for link in links:
#         enhanced_links.append(
#             {
#                 "timestamp": timestamp,
#                 "source": source_url,
#                 "text": link["text"],
#                 "url": link["url"],
#             }
#         )

#     with open(filename, "a", newline="", encoding="utf-8") as file:
#         writer = csv.DictWriter(file, fieldnames=fieldnames)

#         if not file_exists:
#             writer.writeheader()

#         writer.writerows(enhanced_links)


# Save to CSV
source_url = "https://yourstory.com/2025/03/diipa-buller-khoslas-ind-wild-funding-unilever-ventures-sephora"

if __name__ == "__main__":
    asyncio.run(main(source_url))
