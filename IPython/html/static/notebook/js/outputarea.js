// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jqueryui',
    'base/js/utils',
    'base/js/security',
    'base/js/keyboard',
    'notebook/js/mathjaxutils',
    'components/marked/lib/marked',
], function(IPython, $, utils, security, keyboard, mathjaxutils, marked) {
    "use strict";

    /**
     * @class OutputArea
     *
     * @constructor
     */

    var OutputArea = function (options) {
        this.selector = options.selector;
        this.events = options.events;
        this.keyboard_manager = options.keyboard_manager;
        this.wrapper = $(options.selector);
        this.outputs = [];
        this.collapsed = false;
        this.scrolled = false;
        this.scroll_state = 'auto';
        this.trusted = true;
        this.clear_queued = null;
        if (options.prompt_area === undefined) {
            this.prompt_area = true;
        } else {
            this.prompt_area = options.prompt_area;
        }
        this.create_elements();
        this.style();
        this.bind_events();
    };


    /**
     * Class prototypes
     **/

    OutputArea.prototype.create_elements = function () {
        this.element = $("<div/>");
        this.collapse_button = $("<div/>");
        this.prompt_overlay = $("<div/>");
        this.wrapper.append(this.prompt_overlay);
        this.wrapper.append(this.element);
        this.wrapper.append(this.collapse_button);
    };


    OutputArea.prototype.style = function () {
        this.collapse_button.hide();
        this.prompt_overlay.hide();
        
        this.wrapper.addClass('output_wrapper');
        this.element.addClass('output');
        
        this.collapse_button.addClass("btn btn-default output_collapsed");
        this.collapse_button.attr('title', 'click to expand output');
        this.collapse_button.text('. . .');
        
        this.prompt_overlay.addClass('out_prompt_overlay prompt');
        this.prompt_overlay.attr('title', 'click to expand output; double click to hide output');
        
        this.collapse();
    };

    /**
     * Should the OutputArea scroll?
     * Returns whether the height (in lines) exceeds the current threshold.
     * Threshold will be OutputArea.minimum_scroll_threshold if scroll_state=true (manually requested)
     * or OutputArea.auto_scroll_threshold if scroll_state='auto'.
     * This will always return false if scroll_state=false (scroll disabled).
     *
     */
    OutputArea.prototype._should_scroll = function () {
        var threshold;
        if (this.scroll_state === false) {
            return false;
        } else if (this.scroll_state === true) {
            threshold = OutputArea.minimum_scroll_threshold;
        } else {
            threshold = OutputArea.auto_scroll_threshold;
        }
        if (threshold <=0) {
            return false;
        }
        // line-height from http://stackoverflow.com/questions/1185151
        var fontSize = this.element.css('font-size');
        var lineHeight = Math.floor(parseInt(fontSize.replace('px','')) * 1.5);
        return (this.element.height() > threshold * lineHeight);
    };


    OutputArea.prototype.bind_events = function () {
        var that = this;
        this.prompt_overlay.dblclick(function () { that.toggle_output(); });
        this.prompt_overlay.click(function () { that.toggle_scroll(); });

        this.element.resize(function () {
            // FIXME: Firefox on Linux misbehaves, so automatic scrolling is disabled
            if ( utils.browser[0] === "Firefox" ) {
                return;
            }
            // maybe scroll output,
            // if it's grown large enough and hasn't already been scrolled.
            if (!that.scrolled && that._should_scroll()) {
                that.scroll_area();
            }
        });
        this.collapse_button.click(function () {
            that.expand();
        });
    };


    OutputArea.prototype.collapse = function () {
        if (!this.collapsed) {
            this.element.hide();
            this.prompt_overlay.hide();
            if (this.element.html()){
                this.collapse_button.show();
            }
            this.collapsed = true;
            // collapsing output clears scroll state
            this.scroll_state = 'auto';
        }
    };


    OutputArea.prototype.expand = function () {
        if (this.collapsed) {
            this.collapse_button.hide();
            this.element.show();
            if (this.prompt_area) {
                this.prompt_overlay.show();
            }
            this.collapsed = false;
            this.scroll_if_long();
        }
    };


    OutputArea.prototype.toggle_output = function () {
        if (this.collapsed) {
            this.expand();
        } else {
            this.collapse();
        }
    };


    OutputArea.prototype.scroll_area = function () {
        this.element.addClass('output_scroll');
        this.prompt_overlay.attr('title', 'click to unscroll output; double click to hide');
        this.scrolled = true;
    };


    OutputArea.prototype.unscroll_area = function () {
        this.element.removeClass('output_scroll');
        this.prompt_overlay.attr('title', 'click to scroll output; double click to hide');
        this.scrolled = false;
    };

    /**
     * Scroll OutputArea if height exceeds a threshold.
     *
     * Threshold is OutputArea.minimum_scroll_threshold if scroll_state = true,
     * OutputArea.auto_scroll_threshold if scroll_state='auto'.
     *
     **/
    OutputArea.prototype.scroll_if_long = function () {
        var should_scroll = this._should_scroll();
        if (!this.scrolled && should_scroll) {
            // only allow scrolling long-enough output
            this.scroll_area();
        } else if (this.scrolled && !should_scroll) {
            // scrolled and shouldn't be
            this.unscroll_area();
        }
    };


    OutputArea.prototype.toggle_scroll = function () {
        if (this.scroll_state == 'auto') {
            this.scroll_state = !this.scrolled;
        } else {
            this.scroll_state = !this.scroll_state;
        }
        if (this.scrolled) {
            this.unscroll_area();
        } else {
            // only allow scrolling long-enough output
            this.scroll_if_long();
        }
    };


    // typeset with MathJax if MathJax is available
    OutputArea.prototype.typeset = function () {
        utils.typeset(this.element);
    };


    OutputArea.prototype.handle_output = function (msg) {
        var json = {};
        var msg_type = json.output_type = msg.header.msg_type;
        var content = msg.content;
        if (msg_type === "stream") {
            json.text = content.text;
            json.name = content.name;
        } else if (msg_type === "display_data") {
            json.data = content.data;
            json.metadata = content.metadata;
        } else if (msg_type === "execute_result") {
            json.data = content.data;
            json.metadata = content.metadata;
            json.execution_count = content.execution_count;
        } else if (msg_type === "error") {
            json.ename = content.ename;
            json.evalue = content.evalue;
            json.traceback = content.traceback;
        } else {
            console.log("unhandled output message", msg);
            return;
        }
        this.append_output(json);
    };
    
    
    OutputArea.output_types = [
        'application/javascript',
        'text/html',
        'text/markdown',
        'text/latex',
        'image/svg+xml',
        'image/png',
        'image/jpeg',
        'application/pdf',
        'text/plain'
    ];

    OutputArea.prototype.validate_mimebundle = function (bundle) {
        /** scrub invalid outputs */
        if (typeof bundle.data !== 'object') {
            console.warn("mimebundle missing data", bundle);
            bundle.data = {};
        }
        if (typeof bundle.metadata !== 'object') {
            console.warn("mimebundle missing metadata", bundle);
            bundle.metadata = {};
        }
        var data = bundle.data;
        $.map(OutputArea.output_types, function(key){
            if (key !== 'application/json' &&
                data[key] !== undefined &&
                typeof data[key] !== 'string'
            ) {
                console.log("Invalid type for " + key, data[key]);
                delete data[key];
            }
        });
        return bundle;
    };
    
    OutputArea.prototype.append_output = function (json) {
        this.expand();
        
        // Clear the output if clear is queued.
        var needs_height_reset = false;
        if (this.clear_queued) {
            this.clear_output(false);
            needs_height_reset = true;
        }

        var record_output = true;
        switch(json.output_type) {
            case 'execute_result':
                json = this.validate_mimebundle(json);
                this.append_execute_result(json);
                break;
            case 'stream':
                // append_stream might have merged the output with earlier stream output
                record_output = this.append_stream(json);
                break;
            case 'error':
                this.append_error(json);
                break;
            case 'display_data':
                // append handled below
                json = this.validate_mimebundle(json);
                break;
            default:
                console.log("unrecognized output type: " + json.output_type);
                this.append_unrecognized(json);
        }

        // We must release the animation fixed height in a callback since Gecko
        // (FireFox) doesn't render the image immediately as the data is 
        // available.
        var that = this;
        var handle_appended = function ($el) {
            /**
             * Only reset the height to automatic if the height is currently
             * fixed (done by wait=True flag on clear_output).
             */
            if (needs_height_reset) {
                that.element.height('');
            }
            that.element.trigger('resize');
        };
        if (json.output_type === 'display_data') {
            this.append_display_data(json, handle_appended);
        } else {
            handle_appended();
        }
        
        if (record_output) {
            this.outputs.push(json);
        }
    };


    OutputArea.prototype.create_output_area = function () {
        var oa = $("<div/>").addClass("output_area");
        if (this.prompt_area) {
            oa.append($('<div/>').addClass('prompt'));
        }
        return oa;
    };


    function _get_metadata_key(metadata, key, mime) {
        var mime_md = metadata[mime];
        // mime-specific higher priority
        if (mime_md && mime_md[key] !== undefined) {
            return mime_md[key];
        }
        // fallback on global
        return metadata[key];
    }

    OutputArea.prototype.create_output_subarea = function(md, classes, mime) {
        var subarea = $('<div/>').addClass('output_subarea').addClass(classes);
        if (_get_metadata_key(md, 'isolated', mime)) {
            // Create an iframe to isolate the subarea from the rest of the
            // document
            var iframe = $('<iframe/>').addClass('box-flex1');
            iframe.css({'height':1, 'width':'100%', 'display':'block'});
            iframe.attr('frameborder', 0);
            iframe.attr('scrolling', 'auto');

            // Once the iframe is loaded, the subarea is dynamically inserted
            iframe.on('load', function() {
                // Workaround needed by Firefox, to properly render svg inside
                // iframes, see http://stackoverflow.com/questions/10177190/
                // svg-dynamically-added-to-iframe-does-not-render-correctly
                this.contentDocument.open();

                // Insert the subarea into the iframe
                // We must directly write the html. When using Jquery's append
                // method, javascript is evaluated in the parent document and
                // not in the iframe document.  At this point, subarea doesn't
                // contain any user content.
                this.contentDocument.write(subarea.html());

                this.contentDocument.close();

                var body = this.contentDocument.body;
                // Adjust the iframe height automatically
                iframe.height(body.scrollHeight + 'px');
            });

            // Elements should be appended to the inner subarea and not to the
            // iframe
            iframe.append = function(that) {
                subarea.append(that);
            };

            return iframe;
        } else {
            return subarea;
        }
    };


    OutputArea.prototype._append_javascript_error = function (err, element) {
        /**
         * display a message when a javascript error occurs in display output
         */
        var msg = "Javascript error adding output!";
        if ( element === undefined ) return;
        element
            .append($('<div/>').text(msg).addClass('js-error'))
            .append($('<div/>').text(err.toString()).addClass('js-error'))
            .append($('<div/>').text('See your browser Javascript console for more details.').addClass('js-error'));
    };
    
    OutputArea.prototype._safe_append = function (toinsert) {
        /**
         * safely append an item to the document
         * this is an object created by user code,
         * and may have errors, which should not be raised
         * under any circumstances.
         */
        try {
            this.element.append(toinsert);
        } catch(err) {
            console.log(err);
            // Create an actual output_area and output_subarea, which creates
            // the prompt area and the proper indentation.
            var toinsert = this.create_output_area();
            var subarea = $('<div/>').addClass('output_subarea');
            toinsert.append(subarea);
            this._append_javascript_error(err, subarea);
            this.element.append(toinsert);
        }

        // Notify others of changes.
        this.element.trigger('changed');
    };


    OutputArea.prototype.append_execute_result = function (json) {
        var n = json.execution_count || ' ';
        var toinsert = this.create_output_area();
        if (this.prompt_area) {
            toinsert.find('div.prompt').addClass('output_prompt').text('Out[' + n + ']:');
        }
        var inserted = this.append_mime_type(json, toinsert);
        if (inserted) {
            inserted.addClass('output_result');
        }
        this._safe_append(toinsert);
        // If we just output latex, typeset it.
        if ((json.data['text/latex'] !== undefined) ||
            (json.data['text/html'] !== undefined) ||
            (json.data['text/markdown'] !== undefined)) {
            this.typeset();
        }
    };


    OutputArea.prototype.append_error = function (json) {
        var tb = json.traceback;
        if (tb !== undefined && tb.length > 0) {
            var s = '';
            var len = tb.length;
            for (var i=0; i<len; i++) {
                s = s + tb[i] + '\n';
            }
            s = s + '\n';
            var toinsert = this.create_output_area();
            var append_text = OutputArea.append_map['text/plain'];
            if (append_text) {
                append_text.apply(this, [s, {}, toinsert]).addClass('output_error');
            }
            this._safe_append(toinsert);
        }
    };


    OutputArea.prototype.append_stream = function (json) {
        var text = json.text;
        if (typeof text !== 'string') {
            console.error("Stream output is invalid (missing text)", json);
            return false;
        }
        var subclass = "output_"+json.name;
        if (this.outputs.length > 0){
            // have at least one output to consider
            var last = this.outputs[this.outputs.length-1];
            if (last.output_type == 'stream' && json.name == last.name){
                // latest output was in the same stream,
                // so append directly into its pre tag
                // escape ANSI & HTML specials:
                last.text = utils.fixCarriageReturn(last.text + json.text);
                var pre = this.element.find('div.'+subclass).last().find('pre');
                var html = utils.fixConsole(last.text);
                html = utils.autoLinkUrls(html);
                // The only user content injected with this HTML call is
                // escaped by the fixConsole() method.
                pre.html(html);
                // return false signals that we merged this output with the previous one,
                // and the new output shouldn't be recorded.
                return false;
            }
        }

        if (!text.replace("\r", "")) {
            // text is nothing (empty string, \r, etc.)
            // so don't append any elements, which might add undesirable space
            // return true to indicate the output should be recorded.
            return true;
        }

        // If we got here, attach a new div
        var toinsert = this.create_output_area();
        var append_text = OutputArea.append_map['text/plain'];
        if (append_text) {
            append_text.apply(this, [text, {}, toinsert]).addClass("output_stream " + subclass);
        }
        this._safe_append(toinsert);
        return true;
    };


    OutputArea.prototype.append_unrecognized = function (json) {
        var that = this;
        var toinsert = this.create_output_area();
        var subarea = $('<div/>').addClass('output_subarea output_unrecognized');
        toinsert.append(subarea);
        subarea.append(
            $("<a>")
                .attr("href", "#")
                .text("Unrecognized output: " + json.output_type)
                .click(function () {
                    that.events.trigger('unrecognized_output.OutputArea', {output: json});
                })
        );
        this._safe_append(toinsert);
    };


    OutputArea.prototype.append_display_data = function (json, handle_inserted) {
        var toinsert = this.create_output_area();
        if (this.append_mime_type(json, toinsert, handle_inserted)) {
            this._safe_append(toinsert);
            // If we just output latex, typeset it.
            if ((json.data['text/latex'] !== undefined) ||
                (json.data['text/html'] !== undefined) ||
                (json.data['text/markdown'] !== undefined)) {
                this.typeset();
            }
        }
    };


    OutputArea.safe_outputs = {
        'text/plain' : true,
        'text/latex' : true,
        'image/png' : true,
        'image/jpeg' : true
    };
    
    OutputArea.prototype.append_mime_type = function (json, element, handle_inserted) {
        for (var i=0; i < OutputArea.display_order.length; i++) {
            var type = OutputArea.display_order[i];
            var append = OutputArea.append_map[type];
            if ((json.data[type] !== undefined) && append) {
                var value = json.data[type];
                if (!this.trusted && !OutputArea.safe_outputs[type]) {
                    // not trusted, sanitize HTML
                    if (type==='text/html' || type==='text/svg') {
                        value = security.sanitize_html(value);
                    } else {
                        // don't display if we don't know how to sanitize it
                        console.log("Ignoring untrusted " + type + " output.");
                        continue;
                    }
                }
                var md = json.metadata || {};
                var toinsert = append.apply(this, [value, md, element, handle_inserted]);
                // Since only the png and jpeg mime types call the inserted
                // callback, if the mime type is something other we must call the 
                // inserted callback only when the element is actually inserted
                // into the DOM.  Use a timeout of 0 to do this.
                if (['image/png', 'image/jpeg'].indexOf(type) < 0 && handle_inserted !== undefined) {
                    setTimeout(handle_inserted, 0);
                }
                this.events.trigger('output_appended.OutputArea', [type, value, md, toinsert]);
                return toinsert;
            }
        }
        return null;
    };


    var append_html = function (html, md, element) {
        var type = 'text/html';
        var toinsert = this.create_output_subarea(md, "output_html rendered_html", type);
        this.keyboard_manager.register_events(toinsert);
        toinsert.append(html);
        dblclick_to_reset_size(toinsert.find('img'));
        element.append(toinsert);
        return toinsert;
    };


    var append_markdown = function(markdown, md, element) {
        var type = 'text/markdown';
        var toinsert = this.create_output_subarea(md, "output_markdown", type);
        var text_and_math = mathjaxutils.remove_math(markdown);
        var text = text_and_math[0];
        var math = text_and_math[1];
        marked(text, function (err, html) {
            html = mathjaxutils.replace_math(html, math);
            toinsert.append(html);
        });
        dblclick_to_reset_size(toinsert.find('img'));
        element.append(toinsert);
        return toinsert;
    };


    var append_javascript = function (js, md, element) {
        /**
         * We just eval the JS code, element appears in the local scope.
         */
        var type = 'application/javascript';
        var toinsert = this.create_output_subarea(md, "output_javascript", type);
        this.keyboard_manager.register_events(toinsert);
        element.append(toinsert);

        // Fix for ipython/issues/5293, make sure `element` is the area which
        // output can be inserted into at the time of JS execution.
        element = toinsert;
        try {
            eval(js);
        } catch(err) {
            console.log(err);
            this._append_javascript_error(err, toinsert);
        }
        return toinsert;
    };


    var append_text = function (data, md, element) {
        var type = 'text/plain';
        var toinsert = this.create_output_subarea(md, "output_text", type);
        // escape ANSI & HTML specials in plaintext:
        data = utils.fixConsole(data);
        data = utils.fixCarriageReturn(data);
        data = utils.autoLinkUrls(data);
        // The only user content injected with this HTML call is
        // escaped by the fixConsole() method.
        toinsert.append($("<pre/>").html(data));
        element.append(toinsert);
        return toinsert;
    };


    var append_svg = function (svg_html, md, element) {
        var type = 'image/svg+xml';
        var toinsert = this.create_output_subarea(md, "output_svg", type);

        // Get the svg element from within the HTML.
        var svg = $('<div />').html(svg_html).find('svg');
        var svg_area = $('<div />');
        var width = svg.attr('width');
        var height = svg.attr('height');
        svg
            .width('100%')
            .height('100%');
        svg_area
            .width(width)
            .height(height);

        svg_area.append(svg);
        toinsert.append(svg_area);
        element.append(toinsert);

        return toinsert;
    };

    function dblclick_to_reset_size (img) {
        /**
         * Double-click on an image toggles confinement to notebook width
         *
         * img: jQuery element
         */

        img.dblclick(function () {
            // dblclick toggles *raw* size, disabling max-width confinement.
            if (img.hasClass('unconfined')) {
                img.removeClass('unconfined');
            } else {
                img.addClass('unconfined');
            }
        });
    };

    var set_width_height = function (img, md, mime) {
        /**
         * set width and height of an img element from metadata
         */
        var height = _get_metadata_key(md, 'height', mime);
        if (height !== undefined) img.attr('height', height);
        var width = _get_metadata_key(md, 'width', mime);
        if (width !== undefined) img.attr('width', width);
        if (_get_metadata_key(md, 'unconfined', mime)) {
            img.addClass('unconfined');
        }
    };
    
    var append_png = function (png, md, element, handle_inserted) {
        var type = 'image/png';
        var toinsert = this.create_output_subarea(md, "output_png", type);
        var img = $("<img/>");
        if (handle_inserted !== undefined) {
            img.on('load', function(){
                handle_inserted(img);
            });
        }
        img[0].src = 'data:image/png;base64,'+ png;
        set_width_height(img, md, 'image/png');
        dblclick_to_reset_size(img);
        toinsert.append(img);
        element.append(toinsert);
        return toinsert;
    };


    var append_jpeg = function (jpeg, md, element, handle_inserted) {
        var type = 'image/jpeg';
        var toinsert = this.create_output_subarea(md, "output_jpeg", type);
        var img = $("<img/>");
        if (handle_inserted !== undefined) {
            img.on('load', function(){
                handle_inserted(img);
            });
        }
        img[0].src = 'data:image/jpeg;base64,'+ jpeg;
        set_width_height(img, md, 'image/jpeg');
        dblclick_to_reset_size(img);
        toinsert.append(img);
        element.append(toinsert);
        return toinsert;
    };


    var append_pdf = function (pdf, md, element) {
        var type = 'application/pdf';
        var toinsert = this.create_output_subarea(md, "output_pdf", type);
        var a = $('<a/>').attr('href', 'data:application/pdf;base64,'+pdf);
        a.attr('target', '_blank');
        a.text('View PDF');
        toinsert.append(a);
        element.append(toinsert);
        return toinsert;
     };

    var append_latex = function (latex, md, element) {
        /**
         * This method cannot do the typesetting because the latex first has to
         * be on the page.
         */
        var type = 'text/latex';
        var toinsert = this.create_output_subarea(md, "output_latex", type);
        toinsert.append(latex);
        element.append(toinsert);
        return toinsert;
    };


    OutputArea.prototype.append_raw_input = function (msg) {
        var that = this;
        this.expand();
        var content = msg.content;
        var area = this.create_output_area();
        
        // disable any other raw_inputs, if they are left around
        $("div.output_subarea.raw_input_container").remove();
        
        var input_type = content.password ? 'password' : 'text';
        
        area.append(
            $("<div/>")
            .addClass("box-flex1 output_subarea raw_input_container")
            .append(
                $("<span/>")
                .addClass("raw_input_prompt")
                .text(content.prompt)
            )
            .append(
                $("<input/>")
                .addClass("raw_input")
                .attr('type', input_type)
                .attr("size", 47)
                .keydown(function (event, ui) {
                    // make sure we submit on enter,
                    // and don't re-execute the *cell* on shift-enter
                    if (event.which === keyboard.keycodes.enter) {
                        that._submit_raw_input();
                        return false;
                    }
                })
            )
        );
        
        this.element.append(area);
        var raw_input = area.find('input.raw_input');
        // Register events that enable/disable the keyboard manager while raw
        // input is focused.
        this.keyboard_manager.register_events(raw_input);
        // Note, the following line used to read raw_input.focus().focus().
        // This seemed to be needed otherwise only the cell would be focused.
        // But with the modal UI, this seems to work fine with one call to focus().
        raw_input.focus();
    };

    OutputArea.prototype._submit_raw_input = function (evt) {
        var container = this.element.find("div.raw_input_container");
        var theprompt = container.find("span.raw_input_prompt");
        var theinput = container.find("input.raw_input");
        var value = theinput.val();
        var echo  = value;
        // don't echo if it's a password
        if (theinput.attr('type') == 'password') {
            echo = '········';
        }
        var content = {
            output_type : 'stream',
            name : 'stdout',
            text : theprompt.text() + echo + '\n'
        };
        // remove form container
        container.parent().remove();
        // replace with plaintext version in stdout
        this.append_output(content, false);
        this.events.trigger('send_input_reply.Kernel', value);
    };


    OutputArea.prototype.handle_clear_output = function (msg) {
        /**
         * msg spec v4 had stdout, stderr, display keys
         * v4.1 replaced these with just wait
         * The default behavior is the same (stdout=stderr=display=True, wait=False),
         * so v4 messages will still be properly handled,
         * except for the rarely used clearing less than all output.
         */
        this.clear_output(msg.content.wait || false);
    };


    OutputArea.prototype.clear_output = function(wait, ignore_que) {
        if (wait) {

            // If a clear is queued, clear before adding another to the queue.
            if (this.clear_queued) {
                this.clear_output(false);
            }

            this.clear_queued = true;
        } else {

            // Fix the output div's height if the clear_output is waiting for
            // new output (it is being used in an animation).
            if (!ignore_que && this.clear_queued) {
                var height = this.element.height();
                this.element.height(height);
                this.clear_queued = false;
            }
            
            // Clear all
            // Remove load event handlers from img tags because we don't want
            // them to fire if the image is never added to the page.
            this.element.find('img').off('load');
            this.element.html("");

            // Notify others of changes.
            this.element.trigger('changed');
            
            this.outputs = [];
            this.trusted = true;
            this.unscroll_area();
            return;
        }
    };


    // JSON serialization

    OutputArea.prototype.fromJSON = function (outputs, metadata) {
        var len = outputs.length;
        metadata = metadata || {};

        for (var i=0; i<len; i++) {
            this.append_output(outputs[i]);
        }
        if (metadata.collapsed !== undefined) {
            if (metadata.collapsed) {
                this.collapse();
            } else {
                this.expand();
            }
        }
        if (metadata.scrolled !== undefined) {
            this.scroll_state = metadata.scrolled;
            if (metadata.scrolled) {
                this.scroll_if_long();
            } else {
                this.unscroll_area();
            }
        }
    };


    OutputArea.prototype.toJSON = function () {
        return this.outputs;
    };

    /**
     * Class properties
     **/

    /**
     * Threshold to trigger autoscroll when the OutputArea is resized,
     * typically when new outputs are added.
     *
     * Behavior is undefined if autoscroll is lower than minimum_scroll_threshold,
     * unless it is < 0, in which case autoscroll will never be triggered
     *
     * @property auto_scroll_threshold
     * @type Number
     * @default 100
     *
     **/
    OutputArea.auto_scroll_threshold = 100;

    /**
     * Lower limit (in lines) for OutputArea to be made scrollable. OutputAreas
     * shorter than this are never scrolled.
     *
     * @property minimum_scroll_threshold
     * @type Number
     * @default 20
     *
     **/
    OutputArea.minimum_scroll_threshold = 20;


    OutputArea.display_order = [
        'application/javascript',
        'text/html',
        'text/markdown',
        'text/latex',
        'image/svg+xml',
        'image/png',
        'image/jpeg',
        'application/pdf',
        'text/plain'
    ];

    OutputArea.append_map = {
        "text/plain" : append_text,
        "text/html" : append_html,
        "text/markdown": append_markdown,
        "image/svg+xml" : append_svg,
        "image/png" : append_png,
        "image/jpeg" : append_jpeg,
        "text/latex" : append_latex,
        "application/javascript" : append_javascript,
        "application/pdf" : append_pdf
    };

    // For backwards compatability.
    IPython.OutputArea = OutputArea;

    return {'OutputArea': OutputArea};
});
