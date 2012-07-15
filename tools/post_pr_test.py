#!/usr/bin/env python
"""Post the results of a pull request test to Github.
"""
from test_pr import load_results, post_logs, post_results_comment, print_results

num, results, pr, unavailable_pythons = load_results()
results_urls = post_logs(results)
print_results(pr, results_urls, unavailable_pythons)
post_results_comment(pr, results_urls, num, unavailable_pythons)

print()
print("Posted test results to pull request")
print("  " + pr['html_url'])
