#!/usr/bin/env python3
"""
RunPod Endpoint Testing Script for IndexTTS2

This script helps you test your deployed RunPod endpoint with various
emotion combinations and save the resulting audio files.

Usage:
    python test_endpoint.py --endpoint YOUR_ENDPOINT_ID --api-key YOUR_API_KEY
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import requests


def load_test_cases(json_file="test_input.json"):
    """Load test cases from JSON file"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('examples', [])
    except FileNotFoundError:
        print(f"Warning: {json_file} not found. Using default test case.")
        return [{
            "name": "default_test",
            "input": {
                "text": "Hello world! This is a test.",
                "emotion": "calm",
                "intensity": 0.5
            }
        }]


def test_endpoint(endpoint_id, api_key, test_case, save_dir="test_outputs"):
    """
    Test the RunPod endpoint with a single test case

    Args:
        endpoint_id: RunPod endpoint ID
        api_key: RunPod API key
        test_case: Test case dictionary
        save_dir: Directory to save output audio files
    """
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {"input": test_case["input"]}

    print(f"\n{'='*60}")
    print(f"Test: {test_case.get('name', 'Unnamed')}")
    print(f"Description: {test_case.get('description', 'No description')}")
    print(f"Text: {test_case['input']['text'][:50]}...")
    print(f"Emotion: {test_case['input']['emotion']}")
    print(f"Intensity: {test_case['input']['intensity']}")
    print(f"{'='*60}")

    try:
        print("Sending request...", end=" ", flush=True)
        start_time = time.time()

        response = requests.post(url, json=payload, headers=headers, timeout=120)
        elapsed = time.time() - start_time

        print(f"Done! ({elapsed:.2f}s)")

        if response.status_code != 200:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"Response: {response.text}")
            return False

        result = response.json()

        # Check for errors in response
        if "error" in result:
            print(f"❌ API Error: {result['error']}")
            print(f"Error Type: {result.get('error_type', 'Unknown')}")
            return False

        # Success - save audio
        if "audio" in result:
            # Create output directory
            os.makedirs(save_dir, exist_ok=True)

            # Generate filename
            test_name = test_case.get('name', 'test').replace(' ', '_')
            emotion = test_case['input']['emotion']
            intensity = test_case['input']['intensity']
            filename = f"{test_name}_{emotion}_{intensity}.wav"
            filepath = os.path.join(save_dir, filename)

            # Decode and save audio
            audio_data = base64.b64decode(result["audio"])
            with open(filepath, 'wb') as f:
                f.write(audio_data)

            # Print results
            print(f"✅ Success!")
            print(f"   Output: {filepath}")
            print(f"   Size: {len(audio_data):,} bytes ({len(audio_data)/1024:.1f} KB)")

            if "metadata" in result:
                metadata = result["metadata"]
                print(f"   Sample Rate: {metadata.get('sample_rate', 'N/A')} Hz")
                print(f"   Emotion Vector: {metadata.get('emotion_vector', 'N/A')}")
                print(f"   Text Length: {metadata.get('text_length', 'N/A')} chars")

            return True
        else:
            print(f"❌ No audio in response")
            print(f"Response: {json.dumps(result, indent=2)}")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 120 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test IndexTTS2 RunPod endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with specific endpoint
  python test_endpoint.py --endpoint abc123 --api-key YOUR_KEY

  # Test only the quick test case
  python test_endpoint.py --endpoint abc123 --api-key YOUR_KEY --quick

  # Test specific cases by name
  python test_endpoint.py --endpoint abc123 --api-key YOUR_KEY --test "Happy excitement" "Sad reflection"

  # Save outputs to custom directory
  python test_endpoint.py --endpoint abc123 --api-key YOUR_KEY --output my_tests
        """
    )

    parser.add_argument(
        '--endpoint', '-e',
        required=True,
        help='RunPod endpoint ID'
    )

    parser.add_argument(
        '--api-key', '-k',
        required=True,
        help='RunPod API key'
    )

    parser.add_argument(
        '--test', '-t',
        nargs='+',
        help='Specific test case names to run (default: run all)'
    )

    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Run only the quick test case'
    )

    parser.add_argument(
        '--output', '-o',
        default='test_outputs',
        help='Output directory for audio files (default: test_outputs)'
    )

    parser.add_argument(
        '--json',
        default='test_input.json',
        help='JSON file with test cases (default: test_input.json)'
    )

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║         IndexTTS2 RunPod Endpoint Testing Script         ║
╚══════════════════════════════════════════════════════════╝

Endpoint ID: {args.endpoint}
Output Dir:  {args.output}
""")

    # Load test cases
    if args.quick:
        # Quick test only
        test_cases = [{
            "name": "quick_test",
            "description": "Quick verification test",
            "input": {
                "text": "Hello world! This is a quick test.",
                "emotion": "calm",
                "intensity": 0.5
            }
        }]
        print("Running quick test only...\n")
    else:
        test_cases = load_test_cases(args.json)

        # Filter by name if specified
        if args.test:
            test_cases = [
                tc for tc in test_cases
                if tc.get('name') in args.test
            ]
            if not test_cases:
                print(f"❌ No test cases found matching: {args.test}")
                return 1

        print(f"Loaded {len(test_cases)} test case(s)\n")

    # Run tests
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] ", end="")
        success = test_endpoint(
            args.endpoint,
            args.api_key,
            test_case,
            args.output
        )
        results.append((test_case.get('name', f'test_{i}'), success))

        # Small delay between requests
        if i < len(test_cases):
            time.sleep(1)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {success_count}/{total_count} passed")

    if success_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - success_count} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
