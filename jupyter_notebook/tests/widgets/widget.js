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
        ['from jupyter_notebook import widgets',
         'from IPython.display import display, clear_output',
         'print("Success")'].join('\n'));
    this.execute_cell_then(index);

    this.then(function () {
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
    multiset.index = this.append_cell([
        'from IPython.utils.traitlets import Unicode, CInt',
        'class MultiSetWidget(widgets.Widget):',
        '    _view_name = Unicode("MultiSetView", sync=True)',
        '    a = CInt(0, sync=True)',
        '    b = CInt(0, sync=True)',
        '    c = CInt(0, sync=True)',
        '    d = CInt(-1, sync=True)', // See if it sends a full state.
        '    def set_state(self, sync_data):',
        '        widgets.Widget.set_state(self, sync_data)',
        '        self.d = len(sync_data)',
        'multiset = MultiSetWidget()',
        'display(multiset)',
        'print(multiset.model_id)'].join('\n'));
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
    throttle_index = this.append_cell([
        'import time',
        'textbox = widgets.Text()',
        'display(textbox)',
        'textbox._dom_classes = ["my-throttle-textbox"]',
        'def handle_change(name, old, new):',
        '    display(len(new))',
        '    time.sleep(0.5)',
        'textbox.on_trait_change(handle_change, "value")',
        'print(textbox.model_id)'].join('\n'));
    this.execute_cell_then(throttle_index, function(index){
        textbox.model_id = this.get_output_cell(index).text.trim();

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.my-throttle-textbox'), 'Textbox exists.');

        // Send 20 characters
        this.sendKeys('.my-throttle-textbox input', '12345678901234567890');
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


    this.thenEvaluate(function() {
        define('TestWidget', ['widgets/js/widget', 'base/js/utils', 'underscore'], function(widget, utils, _) {
            var floatArray = {
                deserialize: function (value, model) {
                    if (value===null) {return null;}
                    // DataView -> float64 typed array
                    return new Float64Array(value.buffer);
                },
                // serialization automatically handled since the 
                // attribute is an ArrayBuffer view
            };
            
            var floatList = {
                deserialize: function (value, model) {
                    // list of floats -> list of strings
                    return value.map(function(x) {return x.toString()});
                },
                serialize: function(value, model) {
                    // list of strings -> list of floats
                    return value.map(function(x) {return parseFloat(x);})
                }
            };

            var TestWidgetModel = widget.WidgetModel.extend({}, {
                serializers: _.extend({
                    array_list: floatList,
                    array_binary: floatArray
                }, widget.WidgetModel.serializers)
            });
            
            var TestWidgetView = widget.DOMWidgetView.extend({
                render: function () {
                    this.listenTo(this.model, 'msg:custom', this.handle_msg);
                },
                handle_msg: function(content, buffers) {
                    this.msg = [content, buffers];
                }
            });

            return {TestWidgetModel: TestWidgetModel, TestWidgetView: TestWidgetView};
        });
    });

    var testwidget = {};
    this.append_cell_execute_then([
        'from jupyter_notebook import widgets',
        'from IPython.utils.traitlets import Unicode, Instance, List',
        'from IPython.display import display',
        'from array import array',
        'def _array_to_memoryview(x):',
        '    if x is None: return None',
        '    try:',
        '        y = memoryview(x)',
        '    except TypeError:',
        '        # in python 2, arrays do not support the new buffer protocol',
        '        y = memoryview(buffer(x))',
        '    return y',
        'def _memoryview_to_array(x):',
        '    if x is None: return None',
        '    return array("d", x.tobytes())',
        'arrays_binary = {',
        '    "from_json": _memoryview_to_array,',
        '    "to_json": _array_to_memoryview',
        '}',
        '',
        'def _array_to_list(x):',
        '    return list(x)',
        'def _list_to_array(x):',
        '    return array("d",x)',
        'arrays_list = {',
        '    "from_json": _list_to_array,',
        '    "to_json": _array_to_list',
        '}',
        '',
        'class TestWidget(widgets.DOMWidget):',
        '    _model_module = Unicode("TestWidget", sync=True)',
        '    _model_name = Unicode("TestWidgetModel", sync=True)',
        '    _view_module = Unicode("TestWidget", sync=True)',
        '    _view_name = Unicode("TestWidgetView", sync=True)',
        '    array_binary = Instance(array, allow_none=True, sync=True, **arrays_binary)',
        '    array_list = Instance(array, args=("d", [3.0]), allow_none=False, sync=True, **arrays_list)',
        '    msg = {}',
        '    def __init__(self, **kwargs):',
        '        super(widgets.DOMWidget, self).__init__(**kwargs)',
        '        self.on_msg(self._msg)',
        '    def _msg(self, _, content, buffers):',
        '        self.msg = [content, buffers]',
        'x=TestWidget()',
        'display(x)',
        'print(x.model_id)'].join('\n'), function(index){
            testwidget.index = index;
            testwidget.model_id = this.get_output_cell(index).text.trim();
        });
    this.wait_for_widget(testwidget);


    this.append_cell_execute_then('x.array_list = array("d", [1.5, 2.0, 3.1])');
    this.wait_for_widget(testwidget);
    this.then(function() {
        var result = this.evaluate(function(index) {
            var v = IPython.notebook.get_cell(index).widget_views[0];
            var result = v.model.get('array_list');
            var z = result.slice();
            z[0]+="1234";
            z[1]+="5678";
            v.model.set('array_list', z);
            v.touch();
            return result;
        }, testwidget.index);
        this.test.assertEquals(result, ["1.5", "2", "3.1"], "JSON custom serializer kernel -> js");
    });
    
    this.assert_output_equals('print(x.array_list.tolist() == [1.51234, 25678.0, 3.1])',
                              'True', 'JSON custom serializer js -> kernel');

    if (this.slimerjs) {
        this.append_cell_execute_then("x.array_binary=array('d', [1.5,2.5,5])", function() {
            this.evaluate(function(index) {
                var v = IPython.notebook.get_cell(index).widget_views[0];
                var z = v.model.get('array_binary');
                z[0]*=3;
                z[1]*=3;
                z[2]*=3;
                // we set to null so that we recognize the change
                // when we set data back to z
                v.model.set('array_binary', null);
                v.model.set('array_binary', z);
                v.touch();
            }, textwidget.index);
        });
        this.wait_for_widget(testwidget);
        this.assert_output_equals('x.array_binary.tolist() == [4.5, 7.5, 15.0]',
                                  'True\n', 'Binary custom serializer js -> kernel')

        this.append_cell_execute_then('x.send("some content", [memoryview(b"binarycontent"), memoryview("morecontent")])');
        this.wait_for_widget(testwidget);

        this.then(function() {
            var result = this.evaluate(function(index) {
                var v = IPython.notebook.get_cell(index).widget_views[0];
                var d = new TextDecoder('utf-8');
                return {text: v.msg[0], 
                        binary0: d.decode(v.msg[1][0]),
                        binary1: d.decode(v.msg[1][1])};
            }, testwidget.index);
            this.test.assertEquals(result, {text: 'some content', 
                                       binary0: 'binarycontent', 
                                       binary1: 'morecontent'}, 
                              "Binary widget messages kernel -> js");
        });

        this.then(function() {
            this.evaluate(function(index) {
                var v = IPython.notebook.get_cell(index).widget_views[0];
                v.send('content back', [new Uint8Array([1,2,3,4]), new Float64Array([2.1828, 3.14159])])
            }, testwidget.index);
        });
        this.wait_for_widget(testwidget);
        this.assert_output_equals([
            'all([x.msg[0] == "content back",',
            '     x.msg[1][0].tolist() == [1,2,3,4],',
            '     array("d", x.msg[1][1].tobytes()).tolist() == [2.1828, 3.14159]])'].join('\n'),
                                  'True', 'Binary buffers message js -> kernel');
    } else {
        console.log("skipping binary websocket tests on phantomjs");
    }

});
