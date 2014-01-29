//
// Test display of images
//
// The effect of shape metadata is validated,
// using Image(retina=True)
//


// 2x2 black square in b64 jpeg and png
b64_image_data = {
    "image/png" : "b'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAC0lEQVR4nGNgQAYAAA4AAamRc7EA\\nAAAASUVORK5CYII='",
    "image/jpeg" : "b'/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a\\nHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy\\nMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAACAAIDASIA\\nAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA\\nAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3\\nODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm\\np6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA\\nAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx\\nBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK\\nU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3\\nuLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD5/ooo\\noA//2Q=='"
}


casper.notebook_test(function () {
    // this.printLog();
    this.test_img_shape = function(fmt, retina) {
        this.thenEvaluate(function (b64data, retina) {
            IPython.notebook.get_cell(0).clear_output();
            var cell = IPython.notebook.get_cell(0);
            cell.set_text([
                "import base64",
                "from IPython.display import display, Image",
                "data = base64.decodestring(" + b64data + ")",
                "retina = bool(" + retina + ")",
                "display(Image(data, retina=retina))"
            ].join("\n"));
            cell.execute();
        }, {b64data : b64_image_data[fmt], retina : retina ? 1:0 });
        
        this.wait_for_output(0);
        
        this.then(function() {
            var img = this.evaluate(function() {
                // get a summary of the image that was just displayed
                var cell = IPython.notebook.get_cell(0);
                var img = $(cell.output_area.element.find("img")[0]);
                return {
                    src : img.attr("src"),
                    width : img.width(),
                    height : img.height(),
                    width_attr : img.attr("width"),
                    height_attr : img.attr("height")
                };
            });
            var prefix = "Image('" + fmt + "', retina=" + retina + ") ";
            this.test.assertType(img, "object", prefix + "img was displayed");
            this.test.assertEquals(img.src.split(',')[0], "data:" + fmt + ";base64",
                prefix + "data-uri prefix"
            );
            var sz = retina ? 1 : 2;
            var sz_attr = retina ? "1" : undefined;
            this.test.assertEquals(img.height, sz, prefix + "measured height");
            this.test.assertEquals(img.width, sz, prefix + "measured width");
            this.test.assertEquals(img.height_attr, sz_attr, prefix + "height attr");
            this.test.assertEquals(img.width_attr, sz_attr, prefix + "width attr");
        });
    };
    this.test_img_shape("image/png", false);
    this.test_img_shape("image/png", true);
    this.test_img_shape("image/jpeg", false);
    this.test_img_shape("image/jpeg", true);
});
