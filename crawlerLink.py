import asyncio
import os
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import csv


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
        TASK: Extract and format the main content list of links from this webpage.
        
        EXTRACTION INSTRUCTIONS:
        1. Identify the MAIN PURPOSE of this webpage (e.g., transaction list, article directory, product catalog)
        2. Find the PRIMARY LIST OF LINKS that represents the core content of the page
        3. Determine the list's ORGANIZING PRINCIPLE (date, category, alphabetical, etc.)
        
        FORMAT REQUIREMENTS:
        1. INCLUDE ONLY:
           - The main heading that describes the list's content
           - Any subheadings that organize the list
           - Any introductory text describing the list (like "Browse X items...")
           - The COMPLETE list of links with their full text
        
        2. FORMAT as clean markdown with:
           - Main image if it's directly relevant to the list content
           - Main heading with ## 
           - Subheadings with #
           - List items with bullets (*) maintaining their original link format
           - Preserve any dates, IDs, or naming patterns in the original links
        
        3. EXCLUDE:
           - Navigation menus
           - Headers and footers
           - Sidebars and advertisements
           - Search boxes and forms
           - Social media links
           - Any content not directly related to the main list
           - Any content that is in footer
        
        CONTENT:
        {markdown_content}
        """

        # Process with Gemini directly
        response = model.invoke([HumanMessage(content=prompt)])
        content = response.content

        # Print the cleaned result
        # print("Extracted Markdown Content:")
        # print(response.content)

        # Extract links
        links = extract_links_from_markdown(content)

        # Print or process the links
        for link in links:
            print(f"Text: {link['text']}")
            print(f"URL: {link['url']}")
            print("---")

        # Save to CSV
        # with open("extracted_links.csv", "w", newline="", encoding="utf-8") as file:
        #     writer = csv.DictWriter(file, fieldnames=["text", "url"])
        #     writer.writeheader()
        #     writer.writerows(links)


def extract_links_from_markdown(markdown_content):
    # Regex pattern for Markdown links: [text](url)
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    # Find all matches
    matches = re.findall(pattern, markdown_content)

    # Convert matches to a list of dictionaries with text and url
    links = []
    for text, url in matches:
        links.append({"text": text, "url": url})

    return links

url = "https://yourstory.com/category/funding"

if __name__ == "__main__":
    asyncio.run(main(url))
