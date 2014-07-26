// Test image class
casper.notebook_test(function () {
    index = this.append_cell(
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
        'image = widgets.ImageWidget()\n' +
        'image.format = "jpeg"\n' +
        'image.value = data\n' +
        'image.width = "50px"\n' +
        'image.height = "50px"\n' +
        // Set css that will make the image render within the PhantomJS visible
        // window.  If we don't do this, the captured image will be black.
        'image.set_css({"background": "blue", "z-index": "9999", "position": "fixed", "top": "0px", "left": "0px"})\n' + 
        'display(image)\n' + 
        'image.add_class("my-test-image")\n' + 
        'print("Success")\n');
    this.execute_cell_then(image_index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create image executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        var img_sel = '.widget-area .widget-subarea img';
        this.test.assert(this.cell_element_exists(index, img_sel), 'Image exists.');

        // Verify that the image's base64 data has made it into the DOM.
        var img_src = this.cell_element_function(image_index, img_sel, 'attr', ['src']);
        this.test.assert(img_src.indexOf(test_jpg) > -1, 'Image src data exists.');
    });    
});