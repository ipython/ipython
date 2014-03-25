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
        this.trusted = true;
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
        
        this.collapse_button.addClass("btn output_collapsed");
        this.collapse_button.attr('title', 'click to expand output');
        this.collapse_button.text('. . .');
        
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
        this.prompt_overlay.dblclick(function () { that.toggle_output(); });
        this.prompt_overlay.click(function () { that.toggle_scroll(); });

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
        }
    };


    OutputArea.prototype.expand = function () {
        if (this.collapsed) {
            this.collapse_button.hide();
            this.element.show();
            this.prompt_overlay.show();
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
    
    
    OutputArea.prototype.rename_keys = function (data, key_map) {
        var remapped = {};
        for (var key in data) {
            var new_key = key_map[key] || key;
            remapped[new_key] = data[key];
        }
        return remapped;
    };


    OutputArea.output_types = [
        'application/javascript',
        'text/html',
        'text/latex',
        'image/svg+xml',
        'image/png',
        'image/jpeg',
        'application/pdf',
        'text/plain'
    ];

    OutputArea.prototype.validate_output = function (json) {
        // scrub invalid outputs
        // TODO: right now everything is a string, but JSON really shouldn't be.
        // nbformat 4 will fix that.
        $.map(OutputArea.output_types, function(key){
            if (json[key] !== undefined && typeof json[key] !== 'string') {
                console.log("Invalid type for " + key, json[key]);
                delete json[key];
            }
        });
        return json;
    };
    
    OutputArea.prototype.append_output = function (json) {
        this.expand();
        // Clear the output if clear is queued.
        var needs_height_reset = false;
        if (this.clear_queued) {
            this.clear_output(false);
            needs_height_reset = true;
        }
        
        // validate output data types
        json = this.validate_output(json);

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
    }


    OutputArea.prototype._append_javascript_error = function (err, element) {
        // display a message when a javascript error occurs in display output
        var msg = "Javascript error adding output!"
        if ( element === undefined ) return;
        element
            .append($('<div/>').text(msg).addClass('js-error'))
            .append($('<div/>').text(err.toString()).addClass('js-error'))
            .append($('<div/>').text('See your browser Javascript console for more details.').addClass('js-error'));
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
            toinsert.find('div.prompt').addClass('output_prompt').text('Out[' + n + ']:');
        }
        var inserted = this.append_mime_type(json, toinsert);
        if (inserted) {
            inserted.addClass('output_pyout');
        }
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
            var append_text = OutputArea.append_map['text/plain'];
            if (append_text) {
                append_text.apply(this, [s, {}, toinsert]).addClass('output_pyerr');
            }
            this._safe_append(toinsert);
        }
    };


    OutputArea.prototype.append_stream = function (json) {
        // temporary fix: if stream undefined (json file written prior to this patch),
        // default to most likely stdout:
        if (json.stream === undefined){
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
                // The only user content injected with this HTML call is
                // escaped by the fixConsole() method.
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
        var append_text = OutputArea.append_map['text/plain'];
        if (append_text) {
            append_text.apply(this, [text, {}, toinsert]).addClass("output_stream " + subclass);
        }
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


    OutputArea.safe_outputs = {
        'text/plain' : true,
        'text/latex' : true,
        'image/png' : true,
        'image/jpeg' : true
    };
    
    OutputArea.prototype.append_mime_type = function (json, element) {
        for (var type_i in OutputArea.display_order) {
            var type = OutputArea.display_order[type_i];
            var append = OutputArea.append_map[type];
            if ((json[type] !== undefined) && append) {
                var value = json[type];
                if (!this.trusted && !OutputArea.safe_outputs[type]) {
                    // not trusted, sanitize HTML
                    if (type==='text/html' || type==='text/svg') {
                        value = IPython.security.sanitize_html(value);
                    } else {
                        // don't display if we don't know how to sanitize it
                        console.log("Ignoring untrusted " + type + " output.");
                        continue;
                    }
                }
                var md = json.metadata || {};
                var toinsert = append.apply(this, [value, md, element]);
                $([IPython.events]).trigger('output_appended.OutputArea', [type, value, md, toinsert]);
                return toinsert;
            }
        }
        return null;
    };


    var append_html = function (html, md, element) {
        var type = 'text/html';
        var toinsert = this.create_output_subarea(md, "output_html rendered_html", type);
        IPython.keyboard_manager.register_events(toinsert);
        toinsert.append(html);
        element.append(toinsert);
        return toinsert;
    };


    var append_javascript = function (js, md, element) {
        // We just eval the JS code, element appears in the local scope.
        var type = 'application/javascript';
        var toinsert = this.create_output_subarea(md, "output_javascript", type);
        IPython.keyboard_manager.register_events(toinsert);
        element.append(toinsert);
        // FIXME TODO : remove `container element for 3.0` 
        //backward compat, js should be eval'ed in a context where `container` is defined.
        var container = element;
        container.show = function(){console.log('Warning "container.show()" is deprecated.')};
        // end backward compat

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


    var append_svg = function (svg, md, element) {
        var type = 'image/svg+xml';
        var toinsert = this.create_output_subarea(md, "output_svg", type);
        toinsert.append(svg);
        element.append(toinsert);
        return toinsert;
    };


    OutputArea.prototype._dblclick_to_reset_size = function (img) {
        // wrap image after it's loaded on the page,
        // otherwise the measured initial size will be incorrect
        img.on("load", function (){
            var h0 = img.height();
            var w0 = img.width();
            if (!(h0 && w0)) {
                // zero size, don't make it resizable
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
        });
    };
    
    var set_width_height = function (img, md, mime) {
        // set width and height of an img element from metadata
        var height = _get_metadata_key(md, 'height', mime);
        if (height !== undefined) img.attr('height', height);
        var width = _get_metadata_key(md, 'width', mime);
        if (width !== undefined) img.attr('width', width);
    };
    
    var append_png = function (png, md, element) {
        var type = 'image/png';
        var toinsert = this.create_output_subarea(md, "output_png", type);
        var img = $("<img/>").attr('src','data:image/png;base64,'+png);
        set_width_height(img, md, 'image/png');
        this._dblclick_to_reset_size(img);
        toinsert.append(img);
        element.append(toinsert);
        return toinsert;
    };


    var append_jpeg = function (jpeg, md, element) {
        var type = 'image/jpeg';
        var toinsert = this.create_output_subarea(md, "output_jpeg", type);
        var img = $("<img/>").attr('src','data:image/jpeg;base64,'+jpeg);
        set_width_height(img, md, 'image/jpeg');
        this._dblclick_to_reset_size(img);
        toinsert.append(img);
        element.append(toinsert);
        return toinsert;
    };


    var append_pdf = function (pdf, md, element) {
        var type = 'application/pdf';
        var toinsert = this.create_output_subarea(md, "output_pdf", type);
        var a = $('<a/>').attr('href', 'data:application/pdf;base64,'+pdf);
        a.attr('target', '_blank');
        a.text('View PDF')
        toinsert.append(a);
        element.append(toinsert);
        return toinsert;
     }

    var append_latex = function (latex, md, element) {
        // This method cannot do the typesetting because the latex first has to
        // be on the page.
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
                .attr('type', 'text')
                .attr("size", 47)
                .keydown(function (event, ui) {
                    // make sure we submit on enter,
                    // and don't re-execute the *cell* on shift-enter
                    if (event.which === IPython.keyboard.keycodes.enter) {
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
        var container = this.element.find("div.raw_input_container");
        var theprompt = container.find("span.raw_input_prompt");
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
        // msg spec v4 had stdout, stderr, display keys
        // v4.1 replaced these with just wait
        // The default behavior is the same (stdout=stderr=display=True, wait=False),
        // so v4 messages will still be properly handled,
        // except for the rarely used clearing less than all output.
        this.clear_output(msg.content.wait || false);
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
            this.trusted = true;
            this.unscroll_area();
            return;
        };
    };


    // JSON serialization

    OutputArea.prototype.fromJSON = function (outputs) {
        var len = outputs.length;
        var data;

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

    OutputArea.display_order = [
        'application/javascript',
        'text/html',
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
        "image/svg+xml" : append_svg,
        "image/png" : append_png,
        "image/jpeg" : append_jpeg,
        "text/latex" : append_latex,
        "application/javascript" : append_javascript,
        "application/pdf" : append_pdf
    };

    IPython.OutputArea = OutputArea;

    return IPython;

}(IPython));
