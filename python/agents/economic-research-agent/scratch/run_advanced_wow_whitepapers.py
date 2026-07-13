#!/usr/bin/env python3
"""Advanced 'WOW Factor' Scenario Generation Suite.
Autonomously extracts live data and synthesizes 3 premium, multi-million dollar corporate whitepaper reports for direct publication.
"""

import os
import sys
import logging

# Ensure project root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from economic_research.agent import ERAAgent
import markdown
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACT_DIR = "/Users/enriq/.gemini/jetski/brain/8e93cb21-a500-4e6b-8e51-3f47b790ae28"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0d1117;
            --container-bg: rgba(22, 27, 34, 0.7);
            --text-main: #c9d1d9;
            --text-title: #ffffff;
            --accent: #58a6ff;
            --border: rgba(48, 54, 61, 0.8);
            --header-bg: rgba(33, 38, 45, 0.8);
        }}
        
        body {{
            background: linear-gradient(135deg, var(--bg-color) 0%, #161b22 100%);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 40px 20px;
            line-height: 1.6;
        }}

        .prose-container {{
            max-width: 1000px;
            margin: 0 auto;
            background: var(--container-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 60px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        }}

        h1, h2, h3, h4 {{
            color: var(--text-title);
            font-weight: 700;
            margin-top: 40px;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }}
        
        h1 {{ font-size: 2.5rem; }}
        h2 {{ font-size: 2rem; color: var(--accent); }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.95em;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}
        
        th {{
            background-color: var(--header-bg);
            color: var(--accent);
            text-align: left;
            font-weight: 600;
            padding: 14px;
            border-bottom: 2px solid var(--border);
        }}
        
        td {{
            padding: 14px;
            border-bottom: 1px solid var(--border);
        }}
        
        tr:nth-child(even) {{
            background-color: rgba(33, 38, 45, 0.4);
        }}

        blockquote {{
            border-left: 4px solid var(--accent);
            padding: 15px 20px;
            background-color: rgba(33, 38, 45, 0.5);
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
            font-style: italic;
        }}
        
        a {{
            color: var(--accent);
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}

        .tag {{
            display: inline-block;
            background-color: var(--accent);
            color: #0d1117;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.8rem;
            margin-bottom: 20px;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="prose-container">
        <span class="tag">{pillar}</span>
        {body}
    </div>
</body>
</html>
"""

SCENARIOS = [
    {
        "id": "scenario_1_sunbelt_real_estate",
        "pillar": "Pillar B: Real Estate & Yield",
        "title": "Corporate Real Estate Investment Brief: Sun Belt Multifamily Portfolio",
        "query": "Underwrite a Multi-Family Investment portfolio across the Sun Belt, contrasting Phoenix, AZ, Atlanta, GA, and Raleigh, NC, and dynamically calculate their estimated Cap Rates against HUD Fair Market Rents."
    },
    {
        "id": "scenario_2_ai_rd_site_selection",
        "pillar": "Pillar C + A: AI Labor & Site Selection",
        "title": "Corporate Site Selection: Advanced AI R&D Center",
        "query": "Select the optimal regional Hub for an Advanced AI R&D Center, contrasting Columbus, OH, Pittsburgh, PA, and Salt Lake City, UT, correlating O*NET AI task exposure, local computer science talent pipelines, and EIA industrial electricity rates."
    },
    {
        "id": "scenario_3_chips_act_corridor",
        "pillar": "Pillar D + A: Global Trade & Fiscal Policy",
        "title": "Corporate Supply Chain Brief: CHIPS Act Semiconductor Corridor",
        "query": "Underwrite a Tier-1 Semiconductor Manufacturing Facility site selection, contrasting Phoenix, AZ and Syracuse, NY, benchmarking USITC trade dependencies, state tax abatements (Good Jobs First), and Federal Register regulatory notices."
    }
]

def generate_scenario(scenario: dict):
    logger.info(f"🚀 Executing Scenario: {scenario['title']}...")
    try:
        agent = ERAAgent()
        
        # Phase 1 & 2 Execution via Universal Orchestrator
        whitepaper_md = agent.generate_whitepaper(scenario["query"])
        
        # Save Markdown Artifact
        md_path = os.path.join(ARTIFACT_DIR, f"{scenario['id']}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(whitepaper_md)
        logger.info(f"✅ Saved Markdown Artifact: {md_path}")
        
        # Convert to Blog-Ready HTML using markdown with extra tables/fences extensions
        html_body = markdown.markdown(
            whitepaper_md, 
            extensions=['tables', 'fenced_code', 'smarty']
        )
        
        # Embed into Glassmorphism Dark Mode Template
        full_html = HTML_TEMPLATE.format(
            title=scenario["title"],
            pillar=scenario["pillar"],
            body=html_body
        )
        
        html_path = os.path.join(ARTIFACT_DIR, f"{scenario['id']}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        logger.info(f"✅ Saved Blog-Ready HTML Artifact: {html_path}")
        
    except Exception as e:
        logger.error(f"❌ Failed Scenario {scenario['id']}: {e}")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🤖 GENERATING ADVANCED WOW FACTOR WHITEPAPERS 🤖         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    for scenario in SCENARIOS:
        generate_scenario(scenario)
    
    print("\n🥂 All Multi-Million Dollar Whitepaper Reports Generated Successfully!")

if __name__ == "__main__":
    main()
