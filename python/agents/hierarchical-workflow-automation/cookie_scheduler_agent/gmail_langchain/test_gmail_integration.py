# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents.context_cache_config import ContextCacheConfig
'\nTest script for LangChain Gmail integration.\nThis script tests the Gmail functionality without running the full agent workflow.\n'
import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from gmail_manager import gmail_manager

def test_gmail_initialization():
    """Test if LangChain Gmail toolkit initializes correctly."""
    print('=' * 60)
    print('Testing LangChain Gmail Toolkit Initialization')
    print('=' * 60)
    print(f'Gmail Manager Available: {gmail_manager.is_available()}')
    print(f'Available Tools: {gmail_manager.get_available_tools()}')
    if gmail_manager.is_available():
        print('SUCCESS: LangChain Gmail Toolkit initialized successfully!')
        return True
    else:
        print('NOTICE: LangChain Gmail Toolkit not available')
        print('\nTo set up LangChain Gmail integration:')
        print('1. Install dependencies: pip install langchain-community')
        print('2. Create gmail_credentials.json file:')
        print('   - Go to Google Cloud Console')
        print('   - Enable Gmail API')
        print('   - Create OAuth 2.0 Client ID (Desktop Application)')
        print('   - Download and save as gmail_credentials.json')
        print('3. Run OAuth2 authentication flow')
        return False

def test_gmail_search():
    """Test Gmail search functionality."""
    if not gmail_manager.is_available():
        print('Skipping search test - Gmail not available')
        return
    print('\n' + '=' * 60)
    print('Testing Gmail Search Functionality')
    print('=' * 60)
    try:
        result = gmail_manager.search_messages('from:me', max_results=3)
        print(f"Search Status: {result['status']}")
        if result['status'] == 'success':
            print('SUCCESS: Gmail search working!')
            print(f"Query: {result['query']}")
            print('Search completed successfully (results not shown for privacy)')
        else:
            print(f"ERROR: Search failed: {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f'ERROR: Search test failed with exception: {e}')

def test_gmail_send_demo():
    """Demonstrate how email sending would work (without actually sending)."""
    print('\n' + '=' * 60)
    print('Gmail Send Function Demo (No actual email sent)')
    print('=' * 60)
    demo_email = {'to': 'customer@example.com', 'subject': 'Your Cookie Delivery is Scheduled!', 'body': "\n        <html>\n        <body>\n            <h2>Cookie Delivery Confirmation</h2>\n            <p>Dear Valued Customer,</p>\n            \n            <p>We're excited to confirm your cookie delivery!</p>\n            \n            <h3>Delivery Details:</h3>\n            <ul>\n                <li><strong>Order Number:</strong> ORD12345</li>\n                <li><strong>Delivery Date:</strong> September 15, 2025</li>\n                <li><strong>Time Window:</strong> 9:00 AM - 9:30 AM</li>\n                <li><strong>Location:</strong> 123 Main St, Anytown, CA</li>\n            </ul>\n            \n            <h3>Your Order:</h3>\n            <ul>\n                <li>12x Chocolate Chip Cookies</li>\n                <li>6x Oatmeal Raisin Cookies</li>\n            </ul>\n            \n            <h3>Special Haiku for September:</h3>\n            <em>\n                Autumn leaves falling<br>\n                Sweet cookies warm the cool air<br>\n                Joy delivered fresh\n            </em>\n            \n            <p>Thank you for choosing our cookie delivery service!</p>\n            \n            <p>Best regards,<br>\n            The Cookie Delivery Team<br>\n            deliveries@cookiebusiness.com</p>\n        </body>\n        </html>\n        "}
    print('Demo email content:')
    print(f"To: {demo_email['to']}")
    print(f"Subject: {demo_email['subject']}")
    print('Body: HTML formatted confirmation email')
    if gmail_manager.is_available():
        print('\nNOTICE: To actually send this email, uncomment the following line:')
        print('# result = gmail_manager.send_email(**demo_email)')
        print('\nSUCCESS: LangChain Gmail is ready to send real emails!')
    else:
        print('\nNOTICE: Gmail not available - would fall back to dummy email')

def test_gmail_credentials_setup():
    """Test credential file setup and provide guidance."""
    print('\n' + '=' * 60)
    print('Gmail Credentials Setup Check')
    print('=' * 60)
    credentials_file = gmail_manager.credentials_file
    token_file = gmail_manager.token_file
    print(f'Credentials file path: {credentials_file}')
    print(f'Token file path: {token_file}')
    print(f'Credentials file exists: {os.path.exists(credentials_file)}')
    print(f'Token file exists: {os.path.exists(token_file)}')
    if not os.path.exists(credentials_file):
        print('\nCredential Setup Instructions:')
        print('1. Go to Google Cloud Console (console.cloud.google.com)')
        print('2. Enable Gmail API')
        print("3. Go to 'Credentials' section")
        print("4. Click 'Create Credentials' > 'OAuth 2.0 Client ID'")
        print("5. Choose 'Desktop Application'")
        print('6. Download the JSON file')
        print(f'7. Save it as: {credentials_file}')
        print('8. Run this test again to authenticate')

def main():
    """Run all Gmail tests."""
    logging.basicConfig(level=logging.INFO)
    print('LangChain Gmail Integration Test Suite')
    print('=' * 60)
    if test_gmail_initialization():
        test_gmail_search()
    test_gmail_send_demo()
    test_gmail_credentials_setup()
    print('\n' + '=' * 60)
    print('Test Suite Complete')
    print('=' * 60)
    if gmail_manager.is_available():
        print('SUCCESS: LangChain Gmail integration is working!')
        print('The agent can now send real Gmail emails when USE_GMAIL_LANGCHAIN=true')
    else:
        print('NOTICE: LangChain Gmail integration needs setup')
        print('The agent will use dummy email data until Gmail is configured')
if __name__ == '__main__':
    main()