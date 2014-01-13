//----------------------------------------------------------------------------
//  Copyright (C) 2008 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// OutputArea
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 * @submodule OutputArea
 */
var IPython = (function (IPython) {
    "use strict";

    var utils = IPython.utils;

    /**
     * @class OutputArea
     *
     * @constructor
     */

    var OutputArea = function (selector, prompt_area) {
        this.selector = selector;
        this.wrapper = $(selector);
        this.outputs = [];
        this.collapsed = false;
        this.scrolled = false;
        this.clear_queued = null;
        if (prompt_area === undefined) {
            this.prompt_area = true;
        } else {
            this.prompt_area = prompt_area;
        }
        this.create_elements();
        this.style();
        this.bind_events();
    };
    
    OutputArea.prototype.create_elements = function () {
        this.element = $("<div/>");
        this.collapse_button = $("<div/>");
        this.prompt_overlay = $("<div/>");
        this.wrapper.append(this.prompt_overlay);
        this.wrapper.append(this.element);
    };


    OutputArea.prototype.style = function () {

        this.wrapper.addClass('output_wrapper');
        this.element.addClass('output');
        
        this.prompt_overlay.addClass('out_prompt_overlay prompt');
        this.prompt_overlay.attr('title', 'click to expand output; double click to hide output');
        
        this.collapse();
    };

    /**
     * Should the OutputArea scroll?
     * Returns whether the height (in lines) exceeds a threshold.
     *
     * @private
     * @method _should_scroll
     * @param [lines=100]{Integer}
     * @return {Bool}
     *
     */
    OutputArea.prototype._should_scroll = function (lines) {
        if (lines <=0 ){ return }
        if (!lines) {
            lines = 100;
        }
        // line-height from http://stackoverflow.com/questions/1185151
        var fontSize = this.element.css('font-size');
        var lineHeight = Math.floor(parseInt(fontSize.replace('px','')) * 1.5);
        
        return (this.element.height() > lines * lineHeight);
    };


    OutputArea.prototype.bind_events = function () {
        var that = this;
        // this.prompt_overlay.dblclick(function () { that.toggle_output(); });
        // this.prompt_overlay.click(function () { that.toggle_scroll(); });
        this.prompt_overlay.click(function () {
            console.log('hi there');
            that.toggle_output();
        });


        this.element.resize(function () {
            // FIXME: Firefox on Linux misbehaves, so automatic scrolling is disabled
            if ( IPython.utils.browser[0] === "Firefox" ) {
                return;
            }
            // maybe scroll output,
            // if it's grown large enough and hasn't already been scrolled.
            if ( !that.scrolled && that._should_scroll(OutputArea.auto_scroll_threshold)) {
                that.scroll_area();
            }
        });
    };


    OutputArea.prototype.collapse = function () {
        if (!this.collapsed) {
            this.wrapper.css('overflow-y', 'hidden');
            this.wrapper.css('max-height', '30px');
            // this.element.hide();
            // this.prompt_overlay.hide();
            this.collapsed = true;
        }
    };


    OutputArea.prototype.expand = function () {
        if (this.collapsed) {
            // this.element.show();
            // this.prompt_overlay.show();
            this.wrapper.css('max-height', '');
            this.wrapper.css('overflow-y', 'visible');
            this.collapsed = false;
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


    /**
     *
     * Scroll OutputArea if height supperior than a threshold (in lines).
     *
     * Threshold is a maximum number of lines. If unspecified, defaults to
     * OutputArea.minimum_scroll_threshold.
     *
     * Negative threshold will prevent the OutputArea from ever scrolling.
     *
     * @method scroll_if_long
     *
     * @param [lines=20]{Number} Default to 20 if not set,
     * behavior undefined for value of `0`.
     *
     **/
    OutputArea.prototype.scroll_if_long = function (lines) {
        var n = lines | OutputArea.minimum_scroll_threshold;
        if(n <= 0){
            return
        }

        if (this._should_scroll(n)) {
            // only allow scrolling long-enough output
            this.scroll_area();
        }
    };


    OutputArea.prototype.toggle_scroll = function () {
        if (this.scrolled) {
            this.unscroll_area();
        } else {
            // only allow scrolling long-enough output
            this.scroll_if_long();
        }
    };


    // typeset with MathJax if MathJax is available
    OutputArea.prototype.typeset = function () {
        if (window.MathJax){
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
        }
    };


    OutputArea.prototype.handle_output = function (msg) {
        var json = {};
        var msg_type = json.output_type = msg.header.msg_type;
        var content = msg.content;
        if (msg_type === "stream") {
            json.text = content.data;
            json.stream = content.name;
        } else if (msg_type === "display_data") {
            json = content.data;
            json.output_type = msg_type;
            json.metadata = content.metadata;
        } else if (msg_type === "pyout") {
            json = content.data;
            json.output_type = msg_type;
            json.metadata = content.metadata;
            json.prompt_number = content.execution_count;
        } else if (msg_type === "pyerr") {
            json.ename = content.ename;
            json.evalue = content.evalue;
            json.traceback = content.traceback;
        }
        this.append_output(json);
    };

    OutputArea.mime_map = {
        "text/plain" : "text",
        "text/html" : "html",
        "image/svg+xml" : "svg",
        "image/png" : "png",
        "image/jpeg" : "jpeg",
        "text/latex" : "latex",
        "application/json" : "json",
        "application/javascript" : "javascript",
    };
    
    OutputArea.mime_map_r = {
        "text" : "text/plain",
        "html" : "text/html",
        "svg" : "image/svg+xml",
        "png" : "image/png",
        "jpeg" : "image/jpeg",
        "latex" : "text/latex",
        "json" : "application/json",
        "javascript" : "application/javascript",
    };

    OutputArea.prototype.rename_keys = function (data, key_map) {
        var remapped = {};
        for (var key in data) {
            var new_key = key_map[key] || key;
            remapped[new_key] = data[key];
        }
        return remapped;
    };
    

    OutputArea.prototype.append_output = function (json) {
        this.expand();
        // Clear the output if clear is queued.
        var needs_height_reset = false;
        if (this.clear_queued) {
            this.clear_output(false);
            needs_height_reset = true;
        }

        if (json.output_type === 'pyout') {
            this.append_pyout(json);
        } else if (json.output_type === 'pyerr') {
            this.append_pyerr(json);
        } else if (json.output_type === 'display_data') {
            this.append_display_data(json);
        } else if (json.output_type === 'stream') {
            this.append_stream(json);
        }
        this.outputs.push(json);
        
        // Only reset the height to automatic if the height is currently
        // fixed (done by wait=True flag on clear_output).
        if (needs_height_reset) {
            this.element.height('');    
        }

        var that = this;
        setTimeout(function(){that.element.trigger('resize');}, 100);
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
                // not in the iframe document.
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
    }


    OutputArea.prototype._append_javascript_error = function (err, element) {
        // display a message when a javascript error occurs in display output
        var msg = "Javascript error adding output!"
        if ( element === undefined ) return;
        element.append(
            $('<div/>').html(msg + "<br/>" +
                err.toString() +
                '<br/>See your browser Javascript console for more details.'
            ).addClass('js-error')
        );
    };
    
    OutputArea.prototype._safe_append = function (toinsert) {
        // safely append an item to the document
        // this is an object created by user code,
        // and may have errors, which should not be raised
        // under any circumstances.
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
    };


    OutputArea.prototype.append_pyout = function (json) {
        var n = json.prompt_number || ' ';
        var toinsert = this.create_output_area();
        if (this.prompt_area) {
            toinsert.find('div.prompt').addClass('output_prompt').html('Out[' + n + ']:');
        }
        this.append_mime_type(json, toinsert);
        this._safe_append(toinsert);
        // If we just output latex, typeset it.
        if ((json['text/latex'] !== undefined) || (json['text/html'] !== undefined)) {
            this.typeset();
        }
    };


    OutputArea.prototype.append_pyerr = function (json) {
        var tb = json.traceback;
        if (tb !== undefined && tb.length > 0) {
            var s = '';
            var len = tb.length;
            for (var i=0; i<len; i++) {
                s = s + tb[i] + '\n';
            }
            s = s + '\n';
            var toinsert = this.create_output_area();
            this.append_text(s, {}, toinsert);
            this._safe_append(toinsert);
        }
    };


    OutputArea.prototype.append_stream = function (json) {
        // temporary fix: if stream undefined (json file written prior to this patch),
        // default to most likely stdout:
        if (json.stream == undefined){
            json.stream = 'stdout';
        }
        var text = json.text;
        var subclass = "output_"+json.stream;
        if (this.outputs.length > 0){
            // have at least one output to consider
            var last = this.outputs[this.outputs.length-1];
            if (last.output_type == 'stream' && json.stream == last.stream){
                // latest output was in the same stream,
                // so append directly into its pre tag
                // escape ANSI & HTML specials:
                var pre = this.element.find('div.'+subclass).last().find('pre');
                var html = utils.fixCarriageReturn(
                    pre.html() + utils.fixConsole(text));
                pre.html(html);
                return;
            }
        }

        if (!text.replace("\r", "")) {
            // text is nothing (empty string, \r, etc.)
            // so don't append any elements, which might add undesirable space
            return;
        }

        // If we got here, attach a new div
        var toinsert = this.create_output_area();
        this.append_text(text, {}, toinsert, "output_stream "+subclass);
        this._safe_append(toinsert);
    };


    OutputArea.prototype.append_display_data = function (json) {
        var toinsert = this.create_output_area();
        if (this.append_mime_type(json, toinsert)) {
            this._safe_append(toinsert);
            // If we just output latex, typeset it.
            if ((json['text/latex'] !== undefined) || (json['text/html'] !== undefined)) {
                this.typeset();
            }
        }
    };

    OutputArea.display_order = [
        'application/javascript',
        'text/html',
        'text/latex',
        'image/svg+xml',
        'image/png',
        'image/jpeg',
        'text/plain'
    ];

    OutputArea.prototype.append_mime_type = function (json, element) {

        for (var type_i in OutputArea.display_order) {
            var type = OutputArea.display_order[type_i];
            var append = OutputArea.append_map[type];
            if ((json[type] !== undefined) && append) {
                var md = json.metadata || {};
                append.apply(this, [json[type], md, element]);
                return true;
            }
        }
        return false;
    };


    OutputArea.prototype.append_html = function (html, md, element) {
        var type = 'text/html';
        var toinsert = this.create_output_subarea(md, "output_html rendered_html", type);
        IPython.keyboard_manager.register_events(toinsert);
        toinsert.append(html);
        element.append(toinsert);
    };


    OutputArea.prototype.append_javascript = function (js, md, container) {
        // We just eval the JS code, element appears in the local scope.
        var type = 'application/javascript';
        var element = this.create_output_subarea(md, "output_javascript", type);
        IPython.keyboard_manager.register_events(element);
        container.append(element);
        try {
            eval(js);
        } catch(err) {
            console.log(err);
            this._append_javascript_error(err, element);
        }
    };


    OutputArea.prototype.append_text = function (data, md, element, extra_class) {
        var type = 'text/plain';
        var toinsert = this.create_output_subarea(md, "output_text", type);
        // escape ANSI & HTML specials in plaintext:
        data = utils.fixConsole(data);
        data = utils.fixCarriageReturn(data);
        data = utils.autoLinkUrls(data);
        if (extra_class){
            toinsert.addClass(extra_class);
        }
        toinsert.append($("<pre/>").html(data));
        element.append(toinsert);
    };


    OutputArea.prototype.append_svg = function (svg, md, element) {
        var type = 'image/svg+xml';
        var toinsert = this.create_output_subarea(md, "output_svg", type);
        toinsert.append(svg);
        element.append(toinsert);
    };


    OutputArea.prototype._dblclick_to_reset_size = function (img) {
        // schedule wrapping image in resizable after a delay,
        // so we don't end up calling resize on a zero-size object
        var that = this;
        setTimeout(function () {
            var h0 = img.height();
            var w0 = img.width();
            if (!(h0 && w0)) {
                // zero size, schedule another timeout
                that._dblclick_to_reset_size(img);
                return;
            }
            img.resizable({
                aspectRatio: true,
                autoHide: true
            });
            img.dblclick(function () {
                // resize wrapper & image together for some reason:
                img.parent().height(h0);
                img.height(h0);
                img.parent().width(w0);
                img.width(w0);
            });
        }, 250);
    };


    OutputArea.prototype.append_png = function (png, md, element) {
        var type = 'image/png';
        var toinsert = this.create_output_subarea(md, "output_png", type);
        var img = $("<img/>");
        img[0].setAttribute('src','data:image/png;base64,'+png);
        if (md['height']) {
            img[0].setAttribute('height', md['height']);
        }
        if (md['width']) {
            img[0].setAttribute('width', md['width']);
        }
        this._dblclick_to_reset_size(img);
        toinsert.append(img);
        element.append(toinsert);
    };


    OutputArea.prototype.append_jpeg = function (jpeg, md, element) {
        var type = 'image/jpeg';
        var toinsert = this.create_output_subarea(md, "output_jpeg", type);
        var img = $("<img/>").attr('src','data:image/jpeg;base64,'+jpeg);
        if (md['height']) {
            img.attr('height', md['height']);
        }
        if (md['width']) {
            img.attr('width', md['width']);
        }
        this._dblclick_to_reset_size(img);
        toinsert.append(img);
        element.append(toinsert);
    };


    OutputArea.prototype.append_latex = function (latex, md, element) {
        // This method cannot do the typesetting because the latex first has to
        // be on the page.
        var type = 'text/latex';
        var toinsert = this.create_output_subarea(md, "output_latex", type);
        toinsert.append(latex);
        element.append(toinsert);
    };

    OutputArea.append_map = {
        "text/plain" : OutputArea.prototype.append_text,
        "text/html" : OutputArea.prototype.append_html,
        "image/svg+xml" : OutputArea.prototype.append_svg,
        "image/png" : OutputArea.prototype.append_png,
        "image/jpeg" : OutputArea.prototype.append_jpeg,
        "text/latex" : OutputArea.prototype.append_latex,
        "application/json" : OutputArea.prototype.append_json,
        "application/javascript" : OutputArea.prototype.append_javascript,
    };

    OutputArea.prototype.append_raw_input = function (msg) {
        var that = this;
        this.expand();
        var content = msg.content;
        var area = this.create_output_area();
        
        // disable any other raw_inputs, if they are left around
        $("div.output_subarea.raw_input").remove();
        
        area.append(
            $("<div/>")
            .addClass("box-flex1 output_subarea raw_input")
            .append(
                $("<span/>")
                .addClass("input_prompt")
                .text(content.prompt)
            )
            .append(
                $("<input/>")
                .addClass("raw_input")
                .attr('type', 'text')
                .attr("size", 47)
                .keydown(function (event, ui) {
                    // make sure we submit on enter,
                    // and don't re-execute the *cell* on shift-enter
                    if (event.which === utils.keycodes.ENTER) {
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
        IPython.keyboard_manager.register_events(raw_input);
        // Note, the following line used to read raw_input.focus().focus().
        // This seemed to be needed otherwise only the cell would be focused.
        // But with the modal UI, this seems to work fine with one call to focus().
        raw_input.focus();
    }

    OutputArea.prototype._submit_raw_input = function (evt) {
        var container = this.element.find("div.raw_input");
        var theprompt = container.find("span.input_prompt");
        var theinput = container.find("input.raw_input");
        var value = theinput.val();
        var content = {
            output_type : 'stream',
            name : 'stdout',
            text : theprompt.text() + value + '\n'
        }
        // remove form container
        container.parent().remove();
        // replace with plaintext version in stdout
        this.append_output(content, false);
        $([IPython.events]).trigger('send_input_reply.Kernel', value);
    }


    OutputArea.prototype.handle_clear_output = function (msg) {
        this.clear_output(msg.content.wait);
    };


    OutputArea.prototype.clear_output = function(wait) {
        if (wait) {

            // If a clear is queued, clear before adding another to the queue.
            if (this.clear_queued) {
                this.clear_output(false);
            };

            this.clear_queued = true;
        } else {

            // Fix the output div's height if the clear_output is waiting for
            // new output (it is being used in an animation).
            if (this.clear_queued) {
                var height = this.element.height();
                this.element.height(height);
                this.clear_queued = false;
            }
            
            // clear all, no need for logic
            this.element.html("");
            this.outputs = [];
            this.unscroll_area();
            return;
        };
    };


    // JSON serialization

    OutputArea.prototype.fromJSON = function (outputs) {
        var len = outputs.length;
        var data;

        // We don't want to display javascript on load, so remove it from the
        // display order for the duration of this function call, but be sure to
        // put it back in there so incoming messages that contain javascript
        // representations get displayed
        var js_index = OutputArea.display_order.indexOf('application/javascript');
        OutputArea.display_order.splice(js_index, 1);

        for (var i=0; i<len; i++) {
            data = outputs[i];
            var msg_type = data.output_type;
            if (msg_type === "display_data" || msg_type === "pyout") {
                // convert short keys to mime keys
                // TODO: remove mapping of short keys when we update to nbformat 4
                 data = this.rename_keys(data, OutputArea.mime_map_r);
                 data.metadata = this.rename_keys(data.metadata, OutputArea.mime_map_r);
            }
            
            this.append_output(data);
        }

        // reinsert javascript into display order, see note above
        OutputArea.display_order.splice(js_index, 0, 'application/javascript');
    };


    OutputArea.prototype.toJSON = function () {
        var outputs = [];
        var len = this.outputs.length;
        var data;
        for (var i=0; i<len; i++) {
            data = this.outputs[i];
            var msg_type = data.output_type;
            if (msg_type === "display_data" || msg_type === "pyout") {
                  // convert mime keys to short keys
                 data = this.rename_keys(data, OutputArea.mime_map);
                 data.metadata = this.rename_keys(data.metadata, OutputArea.mime_map);
            }
            outputs[i] = data;
        }
        return outputs;
    };


    IPython.OutputArea = OutputArea;

    return IPython;

}(IPython));
