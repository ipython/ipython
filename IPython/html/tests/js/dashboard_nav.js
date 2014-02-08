

casper.get_list_items = function () {
    return this.evaluate(function () {
        return $.makeArray($('.item_link').map(function () {
            return {
                link: $(this).attr('href'),
                label: $(this).find('.item_name').text()
            }
        }));
    });
}

casper.test_items = function (baseUrl) {
    casper.then(function () {
        var items = casper.get_list_items();
        casper.each(items, function (self, item) {
            if (!item.label.match('.ipynb$')) {
                var followed_url = baseUrl+item.link;
                if (!followed_url.match('/\.\.$')) {
                    casper.thenOpen(baseUrl+item.link, function () {
                        casper.wait_for_dashboard();
                        this.test.assertEquals(this.getCurrentUrl(), followed_url, 'Testing dashboard link: '+followed_url);
                        casper.test_items(baseUrl);
                        this.back();
                    });
                }
            }
        });
    });
}

casper.dashboard_test(function () {
    baseUrl = this.get_notebook_server()
    casper.test_items(baseUrl);
})

