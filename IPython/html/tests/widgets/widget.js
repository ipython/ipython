var xor = function (a, b) {return !a ^ !b;}; 
var isArray = function (a) {
    try {
        return Object.toString.call(a) === "[object Array]" || Object.toString.call(a) === "[object RuntimeArray]";
    } catch (e) {
        return Array.isArray(a);
    }
};
var recursive_compare = function(a, b) {
    // Recursively compare two objects.
    var same = true;
    same = same && !xor(a instanceof Object || typeof a == 'object', b instanceof Object || typeof b == 'object');
    same = same && !xor(isArray(a), isArray(b));

    if (same) {
        if (a instanceof Object) {
            var key;
            for (key in a) {
                if (a.hasOwnProperty(key) && !recursive_compare(a[key], b[key])) {
                    same = false;
                    break;
                }
            }
            for (key in b) {
                if (b.hasOwnProperty(key) && !recursive_compare(a[key], b[key])) {
                    same = false;
                    break;
                }
            }
        } else {
            return a === b;
        }    
    }
    
    return same;
};

// Test the widget framework.
casper.notebook_test(function () {
    var index;

    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    this.then(function () {

        // Functions that can be used to test the packing and unpacking APIs
        var that = this;
        var test_pack = function (input) {
            var output = that.evaluate(function(input) {
                var model = new IPython.WidgetModel(IPython.notebook.kernel.widget_manager, undefined);
                var results = model._pack_models(input);
                return results;
            }, {input: input});
            that.test.assert(recursive_compare(input, output), 
                JSON.stringify(input) + ' passed through Model._pack_model unchanged');
        };
        var test_unpack = function (input) {
            that.thenEvaluate(function(input) {
                window.results = undefined;
                var model = new IPython.WidgetModel(IPython.notebook.kernel.widget_manager, undefined);
                model._unpack_models(input).then(function(results) { 
                    window.results = results; 
                });    
            }, {input: input});
            
            that.waitFor(function check() {
                return that.evaluate(function() { 
                    return window.results; 
                }); 
            });
            
            that.then(function() {
                var results = that.evaluate(function() { 
                    return window.results; 
                });
                that.test.assert(recursive_compare(input, results), 
                    JSON.stringify(input) + ' passed through Model._unpack_model unchanged');
            });
        };
        var test_packing = function(input) {
            test_pack(input);
            test_unpack(input);
        };
        
        test_packing({0: 'hi', 1: 'bye'});
        test_packing(['hi', 'bye']);
        test_packing(['hi', 5]);
        test_packing(['hi', '5']);
        test_packing([1.0, 0]);
        test_packing([1.0, false]);
        test_packing([1, false]);
        test_packing([1, false, {a: 'hi'}]);
        test_packing([1, false, ['hi']]);
        test_packing([String('hi'), Date("Thu Nov 13 2014 13:46:21 GMT-0500")])

        // Test multi-set, single touch code.  First create a custom widget.
        this.thenEvaluate(function() {
            var MultiSetView = IPython.DOMWidgetView.extend({
                render: function(){
                    this.model.set('a', 1);
                    this.model.set('b', 2);
                    this.model.set('c', 3);
                    this.touch();
                },
            });
            IPython.WidgetManager.register_widget_view('MultiSetView', MultiSetView);
        }, {});
    });

    // Try creating the multiset widget, verify that sets the values correctly.
    var multiset = {};
    multiset.index = this.append_cell(
        'from IPython.utils.traitlets import Unicode, CInt\n' +
        'class MultiSetWidget(widgets.Widget):\n' +
        '    _view_name = Unicode("MultiSetView", sync=True)\n' +
        '    a = CInt(0, sync=True)\n' +
        '    b = CInt(0, sync=True)\n' +
        '    c = CInt(0, sync=True)\n' +
        '    d = CInt(-1, sync=True)\n' + // See if it sends a full state.
        '    def set_state(self, sync_data):\n' +
        '        widgets.Widget.set_state(self, sync_data)\n'+
        '        self.d = len(sync_data)\n' +
        'multiset = MultiSetWidget()\n' +
        'display(multiset)\n' +
        'print(multiset.model_id)');
    this.execute_cell_then(multiset.index, function(index) {
        multiset.model_id = this.get_output_cell(index).text.trim();
    });

    this.wait_for_widget(multiset);

    index = this.append_cell(
        'print("%d%d%d" % (multiset.a, multiset.b, multiset.c))');
    this.execute_cell_then(index, function(index) {
        this.test.assertEquals(this.get_output_cell(index).text.trim(), '123',
            'Multiple model.set calls and one view.touch update state in back-end.');
    });

    index = this.append_cell(
        'print("%d" % (multiset.d))');
    this.execute_cell_then(index, function(index) {
        this.test.assertEquals(this.get_output_cell(index).text.trim(), '3',
            'Multiple model.set calls sent a partial state.');
    });

    var textbox = {};
    throttle_index = this.append_cell(
        'import time\n' +
        'textbox = widgets.Text()\n' +
        'display(textbox)\n' +
        'textbox._dom_classes = ["my-throttle-textbox"]\n' +
        'def handle_change(name, old, new):\n' +
        '    display(len(new))\n' +
        '    time.sleep(0.5)\n' +
        'textbox.on_trait_change(handle_change, "value")\n' +
        'print(textbox.model_id)');
    this.execute_cell_then(throttle_index, function(index){
        textbox.model_id = this.get_output_cell(index).text.trim();

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.my-throttle-textbox'), 'Textbox exists.');

        // Send 20 characters
        this.sendKeys('.my-throttle-textbox input', '....................');
    });

    this.wait_for_widget(textbox);

    this.then(function () { 
        var outputs = this.evaluate(function(i) {
            return IPython.notebook.get_cell(i).output_area.outputs;
        }, {i : throttle_index});

        // Only 4 outputs should have printed, but because of timing, sometimes
        // 5 outputs will print.  All we need to do is verify num outputs <= 5
        // because that is much less than 20.
        this.test.assert(outputs.length <= 5, 'Messages throttled.');

        // We also need to verify that the last state sent was correct.
        var last_state = outputs[outputs.length-1].data['text/plain'];
        this.test.assertEquals(last_state, "20", "Last state sent when throttling.");
    });
});
