// Test image class
casper.notebook_test(function () {
    "use strict";
    var index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    // Get the temporary directory that the test server is running in.
    var cwd = '';
    index = this.append_cell('!echo $(pwd)');
    this.execute_cell_then(index, function(index){
        cwd = this.get_output_cell(index).text.trim();
    });

    var test_jpg = '/9j/4AAQSkZJRgABAQEASABIAAD//gATQ3JlYXRlZCB3aXRoIEdJTVD/2wBDACAWGBwYFCAcGhwkIiAmMFA0MCwsMGJGSjpQdGZ6eHJmcG6AkLicgIiuim5woNqirr7EztDOfJri8uDI8LjKzsb/2wBDASIkJDAqMF40NF7GhHCExsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsb/wgARCAABAAEDAREAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAAA//EABUBAQEAAAAAAAAAAAAAAAAAAAME/9oADAMBAAIQAxAAAAECv//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAQUCf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQMBAT8Bf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQIBAT8Bf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEABj8Cf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAT8hf//aAAwDAQACAAMAAAAQn//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQMBAT8Qf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQIBAT8Qf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAT8Qf//Z';

    var image_index = this.append_cell(
        'import base64\n' + 
        'data = base64.b64decode("' + test_jpg + '")\n' +
        'image = widgets.Image()\n' +
        'image.format = "jpeg"\n' +
        'image.value = data\n' +
        'image.width = "50px"\n' +
        'image.height = "50px"\n' +
        'display(image)\n' + 
        'print("Success")\n');
    this.execute_cell_then(image_index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create image executed with correct output.');
    });

    // Wait for the widget to actually display.
    var img_selector = '.widget-area .widget-subarea img';
    this.wait_for_element(image_index, img_selector);

    this.then(function(){
        this.test.assert(this.cell_element_exists(image_index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(image_index, img_selector), 'Image exists.');

        // Verify that the image's base64 data has made it into the DOM.
        var img_src = this.cell_element_function(image_index, img_selector, 'attr', ['src']);
        this.test.assert(img_src.indexOf(test_jpg) > -1, 'Image src data exists.');
    });    
});
