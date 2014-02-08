//
// Test the tooltip
//
casper.notebook_test(function () {
    var token = this.evaluate(function() {
        return IPython.tooltip.extract_oir_token("C(");
    });
    this.test.assertEquals(token, ["C"], "tooltip token: C");

    token = this.evaluate(function() {
        return IPython.tooltip.extract_oir_token("MyClass(");
    });
    this.test.assertEquals(token, ["MyClass"], "tooltip token: MyClass");

    token = this.evaluate(function() {
        return IPython.tooltip.extract_oir_token("foo123(");
    });
    this.test.assertEquals(token, ["foo123"], "tooltip token: foo123");
});
