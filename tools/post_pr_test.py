from test_pr import load_results, post_logs, post_results_comment, print_results

num, results, pr = load_results()
results_urls = post_logs(results)
print_results(pr, results_urls)
post_results_comment(pr, results_urls, num)

print()
print("Posted test results to pull request")
print("  " + pr['html_url'])
