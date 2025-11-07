#!/usr/bin/env python3
"""
Test script to check which job boards are working
Run this on PythonAnywhere to see which boards are accessible
"""

import sys
import time
from job_trawler import JobTrawler

def test_job_board(trawler, board_name, search_method, keywords="Python Developer", location="London, UK"):
    """Test a single job board"""
    print(f"\n{'='*60}")
    print(f"Testing {board_name.upper()}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        jobs = search_method(keywords, location, max_results=10)  # Test with small number
        elapsed = time.time() - start_time
        
        if jobs:
            print(f"✅ SUCCESS: Found {len(jobs)} jobs in {elapsed:.2f} seconds")
            if len(jobs) > 0:
                print(f"   Sample job: {jobs[0].get('title', 'N/A')} at {jobs[0].get('company', 'N/A')}")
            return True, len(jobs), elapsed
        else:
            print(f"⚠️  NO JOBS: Method worked but returned 0 jobs in {elapsed:.2f} seconds")
            return True, 0, elapsed
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ FAILED: {error_msg[:200]}")
        if 'ERR_TUNNEL_CONNECTION_FAILED' in error_msg or 'proxy' in error_msg.lower():
            print(f"   → PythonAnywhere proxy restriction (Selenium blocked)")
        elif '403' in error_msg or 'Forbidden' in error_msg:
            print(f"   → Access forbidden (proxy blocked)")
        elif 'timeout' in error_msg.lower():
            print(f"   → Connection timeout")
        return False, 0, 0

def main():
    print("\n" + "="*60)
    print("JOB BOARD CONNECTIVITY TEST")
    print("="*60)
    print("\nThis will test each job board to see which ones work on PythonAnywhere")
    print("Test keywords: 'Python Developer'")
    print("Test location: 'London, UK'")
    print("\n" + "="*60)
    
    trawler = JobTrawler()
    
    results = {}
    
    # Test each board
    test_boards = [
        ('LinkedIn', trawler.search_linkedin),
        ('Indeed', trawler.search_indeed),
        ('Reed', trawler.search_reed),
        ('Monster', trawler.search_monster),
        ('Glassdoor', trawler.search_glassdoor),
        ('TotalJobs', trawler.search_totaljobs),
        ('Adzuna', trawler.search_adzuna),
        ('JobServe', trawler.search_jobserve),
        ('WhatJobs', trawler.search_whatjobs),
    ]
    
    for board_name, search_method in test_boards:
        success, job_count, elapsed = test_job_board(trawler, board_name, search_method)
        results[board_name] = {
            'success': success,
            'jobs_found': job_count,
            'time': elapsed
        }
        time.sleep(2)  # Rate limiting between tests
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    working = [name for name, result in results.items() if result['success'] and result['jobs_found'] > 0]
    working_no_jobs = [name for name, result in results.items() if result['success'] and result['jobs_found'] == 0]
    failed = [name for name, result in results.items() if not result['success']]
    
    print(f"\n✅ WORKING (found jobs): {', '.join(working) if working else 'None'}")
    print(f"⚠️  WORKING (no jobs found): {', '.join(working_no_jobs) if working_no_jobs else 'None'}")
    print(f"❌ FAILED: {', '.join(failed) if failed else 'None'}")
    
    print("\n" + "="*60)
    print("RECOMMENDED CONFIG")
    print("="*60)
    print("\nUpdate config.json to enable only working boards:\n")
    print("{")
    print('  "job_boards": {')
    for board_name in results.keys():
        status = "✅" if board_name in working else ("⚠️" if board_name in working_no_jobs else "❌")
        enable = "true" if board_name in working else "false"
        print(f'    "{board_name.lower()}": {enable},  // {status}')
    print("  }")
    print("}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

