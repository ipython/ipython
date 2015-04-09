
// Test
casper.notebook_test(function () {

    var that = this;
    var set_prompt = function (i, val) {
        that.evaluate(function (i, val) {
            var cell = IPython.notebook.get_cell(i);
            cell.set_input_prompt(val);
        }, [i, val]);
    };

    var get_prompt = function (i) {
        return that.evaluate(function (i) {
            var elem = IPython.notebook.get_cell(i).element;
            return elem.find('div.input_prompt').html();
        }, [i]);
    };

    this.then(function () {
        var a = 'print("a")';
        var index = this.append_cell(a);

        this.test.assertEquals(get_prompt(index), "In&nbsp;[&nbsp;]:", "prompt number is &nbsp; by default");
        set_prompt(index, 2);
        this.test.assertEquals(get_prompt(index), "In&nbsp;[2]:", "prompt number is 2");
        set_prompt(index, 0);
        this.test.assertEquals(get_prompt(index), "In&nbsp;[0]:", "prompt number is 0");
        set_prompt(index, "*");
        this.test.assertEquals(get_prompt(index), "In&nbsp;[*]:", "prompt number is *");
        set_prompt(index, undefined);
        this.test.assertEquals(get_prompt(index), "In&nbsp;[&nbsp;]:", "prompt number is &nbsp;");
        set_prompt(index, null);
        this.test.assertEquals(get_prompt(index), "In&nbsp;[&nbsp;]:", "prompt number is &nbsp;");
    });
});
