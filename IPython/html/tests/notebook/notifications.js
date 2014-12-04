// Test the notification area and widgets

casper.notebook_test(function () {
    var that = this;
    var widget = function (name) {
        return that.evaluate(function (name) {
            return (IPython.notification_area.widget(name) !== undefined);
        }, name);
    };

    var get_widget = function (name) {
        return that.evaluate(function (name) {
            return (IPython.notification_area.get_widget(name) !== undefined);
        }, name);
    };

    var new_notification_widget = function (name) {
        return that.evaluate(function (name) {
            return (IPython.notification_area.new_notification_widget(name) !== undefined);
        }, name);
    };

    var widget_has_class = function (name, class_name) {
        return that.evaluate(function (name, class_name) {
            var w = IPython.notification_area.get_widget(name);
            return w.element.hasClass(class_name);
        }, name, class_name);
    };

    var widget_message = function (name) {
        return that.evaluate(function (name) {
            var w = IPython.notification_area.get_widget(name);
            return w.get_message();
        }, name);
    };

    this.then(function () {
        // check that existing widgets are there
        this.test.assert(get_widget('kernel') && widget('kernel'), 'The kernel notification widget exists');
        this.test.assert(get_widget('notebook') && widget('notbook'), 'The notebook notification widget exists');

        // try getting a non-existant widget
        this.test.assertRaises(get_widget, 'foo', 'get_widget: error is thrown');

        // try creating a non-existant widget
        this.test.assert(widget('bar'), 'widget: new widget is created');

        // try creating a widget that already exists
        this.test.assertRaises(new_notification_widget, 'kernel', 'new_notification_widget: error is thrown');
    });

    // test creating 'info' messages
    this.thenEvaluate(function () {
        var tnw = IPython.notification_area.widget('test');
        tnw.info('test info');
    });
    this.waitUntilVisible('#notification_test', function () {
        this.test.assert(widget_has_class('test', 'info'), 'info: class is correct');
        this.test.assertEquals(widget_message('test'), 'test info', 'info: message is correct');
    });

    // test creating 'warning' messages
    this.thenEvaluate(function () {
        var tnw = IPython.notification_area.widget('test');
        tnw.warning('test warning');
    });
    this.waitUntilVisible('#notification_test', function () {
        this.test.assert(widget_has_class('test', 'warning'), 'warning: class is correct');
        this.test.assertEquals(widget_message('test'), 'test warning', 'warning: message is correct');
    });

    // test creating 'danger' messages
    this.thenEvaluate(function () {
        var tnw = IPython.notification_area.widget('test');
        tnw.danger('test danger');
    });
    this.waitUntilVisible('#notification_test', function () {
        this.test.assert(widget_has_class('test', 'danger'), 'danger: class is correct');
        this.test.assertEquals(widget_message('test'), 'test danger', 'danger: message is correct');
    });

    // test message timeout
    this.thenEvaluate(function () {
        var tnw = IPython.notification_area.widget('test');
        tnw.set_message('test timeout', 1000);
    });
    this.waitUntilVisible('#notification_test', function () {
        this.test.assertEquals(widget_message('test'), 'test timeout', 'timeout: message is correct');
    });
    this.waitWhileVisible('#notification_test', function () {
        this.test.assertEquals(widget_message('test'), '', 'timeout: message was cleared');
    });

    // test click callback
    this.thenEvaluate(function () {
        var tnw = IPython.notification_area.widget('test');
        tnw._clicked = false;
        tnw.set_message('test click', undefined, function () {
            tnw._clicked = true;
            return true;
        });
    });
    this.waitUntilVisible('#notification_test', function () {
        this.test.assertEquals(widget_message('test'), 'test click', 'callback: message is correct');
        this.click('#notification_test');
    });
    this.waitFor(function () {
        return this.evaluate(function () {
            return IPython.notification_area.widget('test')._clicked;
        });
    }, function () {
        this.waitWhileVisible('#notification_test', function () {
            this.test.assertEquals(widget_message('test'), '', 'callback: message was cleared');
        });
    });
});
