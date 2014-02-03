casper.wait_for_list = function () {
    casper.waitForSelector('.list_item');
    // casper.wait(500);
}

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

casper.test_items = function (test, baseUrl) {
    casper.then(function () {
        var items = casper.get_list_items();
        casper.each(items, function (self, item) {
            if (!item.label.match('.ipynb$')) {
                var followed_url = baseUrl+item.link;
                if (!followed_url.match('/\.\.$')) {
                    casper.thenOpen(baseUrl+item.link, function () {
                        casper.wait_for_list();
                        test.assertEquals(this.getCurrentUrl(), followed_url, 'Testing dashboard link: '+followed_url);
                        casper.test_items(test, baseUrl);
                        this.back();
                    });
                }
            }
        });
    });
}

casper.test.begin('Testing dashboard navigation', function (test) {
    var baseUrl = casper.get_notebook_server();
    casper.start(baseUrl);
    casper.echo(baseUrl);
    casper.wait_for_list();
    casper.test_items(test, baseUrl);
    casper.run(function() {
        test.done();
    });
});
