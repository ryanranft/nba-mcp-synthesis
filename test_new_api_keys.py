#!/usr/bin/env python3
"""
Test New API Keys - Verify All Keys Work Correctly

Tests all API keys that were recently generated and stored in the secrets structure.
Since file names haven't changed, applications should load them automatically.

Usage:
    python3 test_new_api_keys.py
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_secrets_loading():
    """Test if secrets can be loaded from the unified secrets manager."""
    print("=" * 70)
    print("TESTING SECRETS LOADING")
    print("=" * 70)
    print()

    try:
        from mcp_server.unified_secrets_manager import load_secrets_hierarchical

        print("✅ Unified secrets manager imported successfully")
        print("Loading secrets for nba-mcp-synthesis production context...")
        print()

        # Load secrets
        success = load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "WORKFLOW")

        if success:
            print("✅ Secrets loaded successfully\n")
            return True
        else:
            print("❌ Failed to load secrets\n")
            return False

    except Exception as e:
        print(f"❌ Error loading secrets: {e}\n")
        return False


def test_google_gemini_api():
    """Test Google/Gemini API key."""
    print("-" * 70)
    print("1. TESTING GOOGLE/GEMINI API KEY")
    print("-" * 70)

    api_key = os.getenv('GOOGLE_API_KEY')

    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        return False

    print(f"✅ API key loaded: {api_key[:10]}...{api_key[-4:]}")

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        # Test with a simple prompt
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Say 'API key works' in 3 words")

        print(f"✅ API call successful!")
        print(f"   Response: {response.text.strip()}")
        return True

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


def test_anthropic_claude_api():
    """Test Anthropic/Claude API key."""
    print("\n" + "-" * 70)
    print("2. TESTING ANTHROPIC/CLAUDE API KEY")
    print("-" * 70)

    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return False

    print(f"✅ API key loaded: {api_key[:10]}...{api_key[-4:]}")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Test with a simple prompt
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say 'API key works' in 3 words"}
            ]
        )

        print(f"✅ API call successful!")
        print(f"   Response: {message.content[0].text.strip()}")
        return True

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


def test_deepseek_api():
    """Test DeepSeek API key."""
    print("\n" + "-" * 70)
    print("3. TESTING DEEPSEEK API KEY")
    print("-" * 70)

    api_key = os.getenv('DEEPSEEK_API_KEY')

    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found in environment")
        return False

    print(f"✅ API key loaded: {api_key[:10]}...{api_key[-4:]}")

    try:
        import requests

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": "Say 'API key works' in 3 words"}
            ],
            "max_tokens": 50
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
            print(f"✅ API call successful!")
            print(f"   Response: {content.strip()}")
            return True
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


def test_openai_api():
    """Test OpenAI API key (existing key, for completeness)."""
    print("\n" + "-" * 70)
    print("4. TESTING OPENAI API KEY (Existing)")
    print("-" * 70)

    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    print(f"✅ API key loaded: {api_key[:10]}...{api_key[-4:]}")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        # Test with a simple prompt
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Say 'API key works' in 3 words"}
            ],
            max_tokens=50
        )

        print(f"✅ API call successful!")
        print(f"   Response: {response.choices[0].message.content.strip()}")
        return True

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


def test_slack_webhook():
    """Test Slack Webhook URL."""
    print("\n" + "-" * 70)
    print("5. TESTING SLACK WEBHOOK URL")
    print("-" * 70)

    webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL not found in environment")
        return False

    print(f"✅ Webhook URL loaded: {webhook_url[:30]}...")

    try:
        import requests

        # Send a test message
        data = {
            "text": "🧪 API Key Test: New Slack webhook is working correctly!"
        }

        response = requests.post(webhook_url, json=data, timeout=10)

        if response.status_code == 200:
            print(f"✅ Webhook call successful!")
            print(f"   Status: {response.status_code}")
            print(f"   Message sent to Slack!")
            return True
        else:
            print(f"❌ Webhook call failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Webhook call failed: {e}")
        return False


def main():
    """Run all API key tests."""
    print("\n")
    print("=" * 70)
    print("API KEY TESTING SUITE")
    print("=" * 70)
    print()
    print("Testing all API keys stored in:")
    print("/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/")
    print("big_cat_bets_simulators/NBA/nba-mcp-synthesis/")
    print(".env.nba_mcp_synthesis.production/")
    print()

    # Load secrets first
    if not test_secrets_loading():
        print("\n❌ Cannot proceed without loading secrets")
        sys.exit(1)

    # Track results
    results = {}

    # Test each API key
    print()
    results['Google/Gemini'] = test_google_gemini_api()
    results['Anthropic/Claude'] = test_anthropic_claude_api()
    results['DeepSeek'] = test_deepseek_api()
    results['OpenAI'] = test_openai_api()
    results['Slack Webhook'] = test_slack_webhook()

    # Print summary
    print("\n")
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for name, status in results.items():
        emoji = "✅" if status else "❌"
        status_text = "WORKING" if status else "FAILED"
        print(f"{emoji} {name}: {status_text}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if failed == 0:
        print()
        print("🎉 All API keys are working correctly!")
        print("   Your applications can now use the new keys without any code changes.")
        print()
        return 0
    else:
        print()
        print(f"⚠️  {failed} test(s) failed. Please check the errors above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())




