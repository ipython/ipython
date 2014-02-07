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

    test_jpg = '/9j/4AAQSkZJRgABAQEASABIAAD//gATQ3JlYXRlZCB3aXRoIEdJTVD/2wBDACAWGBwYFCAcGhwkIiAmMFA0MCwsMGJGSjpQdGZ6eHJmcG6AkLicgIiuim5woNqirr7EztDOfJri8uDI8LjKzsb/2wBDASIkJDAqMF40NF7GhHCExsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsb/wgARCAABAAEDAREAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAAA//EABUBAQEAAAAAAAAAAAAAAAAAAAME/9oADAMBAAIQAxAAAAECv//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAQUCf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQMBAT8Bf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQIBAT8Bf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEABj8Cf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAT8hf//aAAwDAQACAAMAAAAQn//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQMBAT8Qf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQIBAT8Qf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAT8Qf//Z';
    test_results = '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAyADIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDi6KKK+ZP3EKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooA//Z';

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

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea img'),
            'Image exists.');

        // Capture a screenshot of the img element as a base64 string.
        var fs = require('fs');
        capture_filename = cwd + fs.separator + 'captured.jpg';
        this.captureSelector(capture_filename, '.my-test-image');
        var stream = fs.open(capture_filename, 'rb');
        var captured = btoa(stream.read());
        stream.close();
        fs.remove(capture_filename);

        // Uncomment line below to output captured image data to a text file.
        // fs.write('./captured.txt', captured, 'w');

        this.test.assertEquals(test_results, captured, "Red image data displayed correctly.");
    });    
});