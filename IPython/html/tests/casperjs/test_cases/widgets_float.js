// Test widget float class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var float_text = {};
    float_text.query = '.widget-area .widget-subarea .widget-hbox-single .my-second-float-text';
    float_text.index = this.append_cell(
        'float_widget = widgets.FloatTextWidget()\n' +
        'display(float_widget)\n' + 
        'float_widget.add_class("my-second-float-text")\n' + 
        'print(float_widget.model_id)\n');
    this.execute_cell_then(float_text.index, function(index){
        float_text.model_id = this.get_output_cell(index).text.trim();
        
        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, float_text.query),
            'Widget float textbox exists.');

        this.cell_element_function(float_text.index, float_text.query, 'val', ['']);
        this.sendKeys(float_text.query, '1.05');
    });

    this.wait_for_widget(float_text);

    index = this.append_cell('print(float_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '1.05\n', 
            'Float textbox value set.');
        this.cell_element_function(float_text.index, float_text.query, 'val', ['']);
        this.sendKeys(float_text.query, '123456789.0');
    });

    this.wait_for_widget(float_text);
    
    index = this.append_cell('print(float_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '123456789.0\n', 
            'Long float textbox value set (probably triggers throttling).');
        this.cell_element_function(float_text.index, float_text.query, 'val', ['']);
        this.sendKeys(float_text.query, '12hello');
    });

    this.wait_for_widget(float_text);

    index = this.append_cell('print(float_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '12.0\n', 
            'Invald float textbox value caught and filtered.');
    });

    var float_text_query = '.widget-area .widget-subarea .widget-hbox-single .widget-numeric-text';
    var slider = {};
    slider.query = '.widget-area .widget-subarea .widget-hbox-single .slider';
    slider.index = this.append_cell(
        'floatrange = [widgets.BoundedFloatTextWidget(), \n' +
        '    widgets.FloatSliderWidget()]\n' +
        '[display(floatrange[i]) for i in range(2)]\n' + 
        'print("Success")\n');
    this.execute_cell_then(slider.index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create float range cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, slider.query),
            'Widget slider exists.');

        this.test.assert(this.cell_element_exists(index, float_text_query),
            'Widget float textbox exists.');
    });

    index = this.append_cell(
        'for widget in floatrange:\n' +
        '    widget.max = 50.0\n' +
        '    widget.min = -50.0\n' +
        '    widget.value = 25.0\n' +
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Float range properties cell executed with correct output.');

        this.test.assert(this.cell_element_exists(slider.index, slider.query), 
            'Widget slider exists.');

        this.test.assert(this.cell_element_function(slider.index, slider.query, 
            'slider', ['value']) == 25.0,
            'Slider set to Python value.');
    });
});