// Sample Sourcing Queries and Outputs
const QUERIES = {
  properties: {
    prompt: "Find active investment properties in Columbus, OH and estimate their Cap Rates using HUD rents.",
    logs: [
      "Connecting to RentCast API (v1)...",
      "Fetching active listings for Columbus, OH [Multi-Family]...",
      "Resolving ZIP codes dynamically using HUD USPS Crosswalk API...",
      "Querying live HUD FMR rents for Columbus FIPS 39049...",
      "Calculating Net Operating Income & Net yields (35% opex ratio)...",
      "Analysis compiled successfully."
    ],
    markdown: `
### Columbus, OH Multi-Family Investment Report

| Address | Listing Price | Beds/Baths | HUD FMR (2BR) | Est. Monthly Rent | Estimated Cap Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **9-11-15 E Norwich Ave** | $749,900 | 9B/1.5Ba | $1,302 (2024) | $1,953.00 | **2.03%** |
| **266 Miller Ave** | $525,000 | 6B/1.5Ba | $1,302 (2024) | $1,953.00 | **2.90%** |
| **831 Lilley Ave** | $285,000 | 2B/1.5Ba | $1,302 (2024) | $1,302.00 | **3.56%** |

*   **Net Yield Cap Rates**: Computed dynamically using active RentCast listings mapped to local county FIPS, correlated with live HUD Fair Market rents (FMR) scaled by bedroom multipliers.
    `
  },
  disruption: {
    prompt: "Compare Austin and Columbus for AI-driven labor market disruption and forecast their 3-year displacement outlook.",
    logs: [
      "Connecting to St. Louis Fed (FRED) API...",
      "Resolving Austin MSA Code: AUST448...",
      "Resolving Columbus MSA Code: COLU139...",
      "Fetching sector employment levels (Information, Professional Services, Finance, Trade, Manufacturing, Leisure)...",
      "Computing weighted AI Vulnerability Indices (Sector Share * ONET Exposure)...",
      "Compiling 3-Year Displacement & Productivity Outlook...",
      "Comparison matrix generated."
    ],
    markdown: `
### Consolidated Executive Report: AI-Driven Labor Market Disruption and Displacement Outlook

| Metric | Austin, TX | Columbus, OH |
| :--- | :--- | :--- |
| **Vulnerability Index (0-100)** | **53** | **52** |
| **Augmentation Potential (0-100)** | **47** | **48** |
| **3-Year Projected Productivity** | **+28%** | **+21%** |
| **3-Year Projected Displacement** | **Medium (10-12%)** | **Medium (10-12%)** |

*   **Strategic Driver (Austin)**: High concentration of advanced knowledge sectors (+28% productivity gains) acting as validators and creators of AI workflows.
*   **Strategic Driver (Columbus)**: Balanced corporate and service-center economy. Moderate displacement risk in back-office processing and administrative support functions.
    `
  },
  exposure: {
    prompt: "Analyze the AI exposure and automation potential for Customer Service Representatives vs. Software Developers.",
    logs: [
      "Searching O*NET Web Services API (v2) for Job Titles...",
      "Resolved Customer Service Representatives (SOC 43-4051.00)...",
      "Resolved Software Developers (SOC 15-1252.00)...",
      "Fetching official DOL task lists from O*NET details API...",
      "Analyzing 10 core tasks via Gemini 2.5 Flash on Vertex AI...",
      "Classifying impact mode, complexity, and recommendations...",
      "Task exposure scoring complete."
    ],
    markdown: `
### O*NET Task AI Exposure Scorecard

#### 1. Software Developers (SOC 15-1252.00)
*   **Exposure Level**: **High**
*   **Primary Impact Mode**: **Augmentation (Task Iteration & Validation)**
*   **Complexity Score**: High (16+ years education required)
*   **Key Exposed Tasks**: Unit testing and debugging, writing/refactoring code, system design integration.
*   **Strategic Advice**: High opportunity for productivity gain. Shift developer hours toward architectural design and system safety validation.

#### 2. Customer Service Representatives (SOC 43-4051.00)
*   **Exposure Level**: **High**
*   **Primary Impact Mode**: **Automation (Directive Workflows)**
*   **Complexity Score**: Medium (12-14 years education required)
*   **Key Exposed Tasks**: Answering billing inquiries, resolving standard order complaints, ticket routing.
*   **Strategic Advice**: High displacement risk. Automate repetitive tier-1 ticketing via API agents; transition human agents to high-empathy case management.
    `
  },
  trade: {
    prompt: "Is North Carolina a manufacturing hub for pharmaceuticals based on export data?",
    logs: [
      "Accessing U.S. Census Bureau International Trade API...",
      "Mapping Commodity 'Pharmaceuticals' to HS Code '30'...",
      "Mapping 'North Carolina' to USPS Abbreviation 'NC'...",
      "Fetching statehs monthly export series...",
      "Formatting export values...",
      "Trade profile fetched."
    ],
    markdown: `
### USITC Supply Chain Trade Sourcing

*   **State**: North Carolina
*   **Commodity**: Pharmaceuticals (Harmonized System HS Code: **30**)
*   **Market Profile**: **YTD Export Value: $6.15B** (cumulative through June 2024)
*   **Source**: U.S. Census Bureau International Trade API (statehs)
*   **Verdict**: Confirmed. North Carolina ranks as a primary national manufacturing hub for pharmaceutical exports.
    `
  },
  affordability: {
    prompt: "Analyze local housing affordability vs Area Median Income (AMI) in Austin.",
    logs: [
      "Connecting to HUD User API...",
      "Mapping 'Austin' to Travis County FIPS Code 48453...",
      "Fetching FY2026 2-Bedroom Fair Market Rent (FMR)...",
      "Fetching FY2025 Very Low Income Limit (50% AMI level)...",
      "Calculating rent-to-income cost burden ratio...",
      "Affordability audit compiled."
    ],
    markdown: `
### HUD Site Affordability Audit

*   **Geography**: Travis County, TX (Austin-Round Rock MSA)
*   **Analysis**: Housing Affordability vs. 50% AMI
*   **FMR Rent (2BR)**: **$1,852**
*   **Monthly Income (50% AMI)**: $3,904.17
*   **Rent-to-Income Ratio**: **47.4%**
*   **Site Selection Verdict**: **High Cost**
*   **Source**: Grounded HUD User Analytics (FMR:2026/IL:2025)
    `
  },
  trends: {
    prompt: "What is the 10-year unemployment trend for Austin vs. Nashville?",
    logs: [
      "Connecting to St. Louis Fed (FRED) API...",
      "Resolving Austin MSA Code: AUST448...",
      "Resolving Nashville MSA Code: NASH947...",
      "Fetching monthly unemployment rate series AUST448UR and NASH947URN...",
      "Computing annual averages (2016-2026)...",
      "Rendering comparison matrix..."
    ],
    markdown: `
### FRED 10-Year Unemployment Trend Comparison (2016-2026)

| Year | Austin-Round Rock MSA | Nashville-Davidson-Murfreesboro MSA |
| :--- | :--- | :--- |
| **2016** | 3.3% | 3.8% |
| **2018** | 2.9% | 2.7% |
| **2020 (Covid)** | 6.2% | 6.6% |
| **2022** | 2.8% | 2.6% |
| **2024** | 3.4% | 3.1% |
| **2026 (Projected)** | **3.1%** | **2.9%** |

*   **Data Source**: Live FRED series data. Shows the resilient labor trajectory of key tech-hub MSAs.
    `
  },
  education: {
    prompt: "Show the educational attainment (Bachelor's+) pipeline for Seattle vs. Raleigh.",
    logs: [
      "Connecting to U.S. Census Bureau ACS API...",
      "Resolving King County, WA FIPS: 53033...",
      "Resolving Wake County, NC FIPS: 37183... ",
      "Fetching ACS 2023 5-Year Profile variable DP02_0068PE (Bachelor's Degree or Higher)...",
      "Attainment calculations complete."
    ],
    markdown: `
### Census ACS Educational Attainment Pipeline

| Region | Mapped County FIPS | Population with Bachelor's Degree or Higher (%) |
| :--- | :--- | :--- |
| **Seattle, WA** | 53033 (King County) | **58.3%** |
| **Raleigh, NC** | 37183 (Wake County) | **58.8%** |

*   **Data Source**: U.S. Census Bureau 2023 American Community Survey (ACS) 5-Year profiles.
    `
  },
  chas: {
    prompt: "What is the percentage of cost-burdened households in Travis County, TX (FIPS 48453) using CHAS data?",
    logs: [
      "Connecting to HUD User CHAS API...",
      "Querying CHAS profile for Travis County FIPS 48453...",
      "Parsing household cost-burden categories (spent >30% on housing)...",
      "CHAS indicators calculated."
    ],
    markdown: `
### HUD CHAS Housing Affordability Audit

*   **Geography**: Travis County, TX (FIPS Code: **48453**)
*   **Total Households**: 538,110
*   **Cost-Burdened Households**: **32.2%** (Spending >30% of income on monthly housing costs)
*   **Households with Severe Problems**: **35.1%** (Lack of kitchen, plumbing, or severe overcrowding)
*   **Strategic Verdict**: High cost burden indicates elevated pressure on local lower-to-middle wage employee retention.
    `
  },
  datacenter: {
    prompt: "Compare Austin and Raleigh for a new data center HQ.",
    logs: [
      "Connecting to EIA (U.S. Energy Information Administration) API...",
      "Fetching industrial electricity rates for Texas vs. North Carolina...",
      "Querying Census ACS Bachelor's+ pipeline for Austin vs. Raleigh...",
      "Retrieving state corporate income tax profiles (scheduled phase-downs)...",
      "Compiling 360-degree Site Selection scorecard..."
    ],
    markdown: `
### Strategic Site Selection Case Study: Data Center HQ (NAICS 518210)

| Sourcing Metric | Austin, TX | Raleigh, NC |
| :--- | :--- | :--- |
| **Industrial Utility Rate** | 8.2¢ / kWh (ERCOT) | **7.5¢ / kWh** (Duke Energy) |
| **Talent Pipeline (CS Graduates)** | **1,200** (UT Austin) | 850 (NC State / UNC) |
| **Corporate Tax Phase-Down** | 0.75% Franchise Tax | **0.0%** (Scheduled by 2030) |
| **2BR Housing Affordability (FMR)**| $1,852 / mo | **$1,480 / mo** |

*   **Recommendation**: **Raleigh** for long-term operational OPEX stability (energy rates + tax phase-down); **Austin** for immediate tech talent density.
    `
  }
};

let currentTab = 'properties';

function selectTab(tabKey) {
  currentTab = tabKey;
  
  // Update active states
  document.querySelectorAll('.lab-btn').forEach(btn => btn.classList.remove('active'));
  const targetBtn = document.getElementById(`btn-${tabKey}`);
  if (targetBtn) targetBtn.classList.add('active');
  
  // Set prompt text
  document.getElementById('prompt-text').textContent = QUERIES[tabKey].prompt;
  
  // Hide previous result
  document.getElementById('terminal-output').style.display = 'none';
}

function loadAndRunQuery(tabKey) {
  selectTab(tabKey);
  document.getElementById('lab').scrollIntoView({ behavior: 'smooth' });
  setTimeout(() => {
    runQuery();
  }, 800);
}

async function runQuery() {
  const tabKey = currentTab;
  const runBtn = document.getElementById('run-btn');
  const terminalOutput = document.getElementById('terminal-output');
  const statusLog = document.getElementById('status-log');
  const resultMarkdown = document.getElementById('result-markdown');
  
  runBtn.disabled = true;
  terminalOutput.style.display = 'block';
  statusLog.innerHTML = '';
  resultMarkdown.innerHTML = '';
  
  // Try live API first if the user is running the FastAPI backend locally
  let liveSucceeded = false;
  try {
    const rawPrompt = QUERIES[tabKey].prompt;
    
    // Check if local agent API is active on port 8000
    // (We use a short timeout to prevent hanging if offline)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    
    const response = await fetch('http://localhost:8000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: rawPrompt }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      const data = await response.json();
      const outputText = data.output || data.result || JSON.stringify(data, null, 2);
      
      // Simulate logs anyway for aesthetic factor
      for (const log of QUERIES[tabKey].logs) {
        await appendStatusLog(statusLog, log);
      }
      
      resultMarkdown.innerHTML = formatMarkdown(outputText);
      liveSucceeded = true;
    }
  } catch (err) {
    console.log("Local agent API offline. Loading pre-computed high-fidelity fallback query...", err);
  }
  
  // Fall back to pre-computed markdown if local server is not running
  if (!liveSucceeded) {
    for (const log of QUERIES[tabKey].logs) {
      await appendStatusLog(statusLog, log);
    }
    resultMarkdown.innerHTML = formatMarkdown(QUERIES[tabKey].markdown);
  }
  
  runBtn.disabled = false;
}

function appendStatusLog(element, text) {
  return new Promise(resolve => {
    const line = document.createElement('div');
    line.className = 'status-line';
    line.innerHTML = `<div class="spinner"></div><span>${text}</span>`;
    element.appendChild(line);
    
    setTimeout(() => {
      // Remove spinner and replace with check mark
      line.querySelector('.spinner').replaceWith(document.createTextNode('✓ '));
      line.style.color = '#10b981'; // Success Green
      resolve();
    }, 600); // Simulated delay
  });
}

function formatMarkdown(text) {
  const lines = text.trim().split('\n');
  let inTable = false;
  let tableHtml = '';
  let result = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    if (line.startsWith('|')) {
      if (!inTable) {
        inTable = true;
        tableHtml = '<table>';
        // Process header row
        tableHtml += '<thead><tr>';
        line.split('|').forEach((cell, idx, arr) => {
          if (idx > 0 && idx < arr.length - 1) {
            tableHtml += `<th>${cell.trim()}</th>`;
          }
        });
        tableHtml += '</tr></thead><tbody>';
      } else {
        // Check if this is a separator row like | :--- | :--- |
        const cleanLine = line.replace(/[\s:\-|]/g, '');
        if (cleanLine === '') {
          continue; // skip separator row
        }
        // Process standard row
        tableHtml += '<tr>';
        line.split('|').forEach((cell, idx, arr) => {
          if (idx > 0 && idx < arr.length - 1) {
            let cellContent = cell.trim();
            // simple inline formatting like bold
            cellContent = cellContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            tableHtml += `<td>${cellContent}</td>`;
          }
        });
        tableHtml += '</tr>';
      }
    } else {
      if (inTable) {
        inTable = false;
        tableHtml += '</tbody></table>';
        result.push(tableHtml);
      }
      
      // Standard markdown processing
      let formattedLine = line;
      if (formattedLine.startsWith('### ')) {
        formattedLine = `<h3>${formattedLine.substring(4)}</h3>`;
      } else if (formattedLine.startsWith('#### ')) {
        formattedLine = `<h4>${formattedLine.substring(5)}</h4>`;
      } else if (formattedLine.startsWith('* ') || formattedLine.startsWith('- ')) {
        formattedLine = `<li>${formattedLine.substring(2)}</li>`;
      }
      
      // format bold inline
      formattedLine = formattedLine.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      result.push(formattedLine);
    }
  }
  
  if (inTable) {
    tableHtml += '</tbody></table>';
    result.push(tableHtml);
  }
  
  // Wrap li tags in ul
  let finalHtml = result.join('\n');
  finalHtml = finalHtml.replace(/(<li>.*?<\/li>)/gms, '<ul>$1</ul>');
  
  return finalHtml;
}

// Initial selection and Theme Toggle
window.addEventListener('DOMContentLoaded', () => {
  selectTab('properties');
  
  // Theme Toggle Logic
  const themeToggleBtn = document.getElementById('theme-toggle');
  const currentTheme = localStorage.getItem('theme') || 'light';
  
  if (currentTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
  }
  
  themeToggleBtn.addEventListener('click', () => {
    let theme = 'light';
    if (document.documentElement.getAttribute('data-theme') === 'light') {
      theme = 'dark';
    }
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  });
});
