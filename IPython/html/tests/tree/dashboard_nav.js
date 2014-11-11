

casper.get_list_items = function () {
    return this.evaluate(function () {
        return $.makeArray($('.item_link').map(function () {
            return {
                link: $(this).attr('href'),
                label: $(this).find('.item_name').text()
            };
        }));
    });
};

casper.test_items = function (baseUrl, visited) {
    visited = visited || {};
    casper.then(function () {
        var items = casper.get_list_items();
        casper.each(items, function (self, item) {
            if (item.link.match(/^\/tree\//)) {
                var followed_url = baseUrl+item.link;
                if (!visited[followed_url]) {
                    visited[followed_url] = true;
                    casper.thenOpen(followed_url, function () {
                        this.waitFor(this.page_loaded);
                        casper.wait_for_dashboard();
                        // getCurrentUrl is with host, and url-decoded,
                        // but item.link is without host, and url-encoded
                        var expected = baseUrl + decodeURIComponent(item.link);
                        this.test.assertEquals(this.getCurrentUrl(), expected, 'Testing dashboard link: ' + expected);
                        casper.test_items(baseUrl, visited);
                        this.back();
                    });
                }
            }
        });
    });
};

casper.dashboard_test(function () {
    baseUrl = this.get_notebook_server();
    casper.test_items(baseUrl);
});

