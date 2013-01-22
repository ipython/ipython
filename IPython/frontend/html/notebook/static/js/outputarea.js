//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// OutputArea
//============================================================================

var IPython = (function (IPython) {
    "use strict";

    var utils = IPython.utils;

    var OutputArea = function (selector, prompt_area) {
        this.selector = selector;
        this.wrapper = $(selector);
        this.outputs = [];
        this.collapsed = false;
        this.scrolled = false;
        this.clear_out_timeout = null;
        if (prompt_area === undefined) {
            this.prompt_area = true;
        } else {
            this.prompt_area = prompt_area;
        };
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
        this.wrapper.append(this.collapse_button);
    };


    OutputArea.prototype.style = function () {
        this.collapse_button.hide();
        this.prompt_overlay.hide();
        
        this.wrapper.addClass('output_wrapper');
        this.element.addClass('output vbox');
        
        this.collapse_button.button();
        this.collapse_button.addClass('output_collapsed vbox');
        this.collapse_button.attr('title', 'click to expand outout');
        this.collapse_button.html('. . .');
        
        this.prompt_overlay.addClass('out_prompt_overlay prompt');
        this.prompt_overlay.attr('title', 'click to expand outout; double click to hide output');
        
        this.collapse();
    };


    OutputArea.prototype._should_scroll = function (lines) {
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
            if ( !that.scrolled && that._should_scroll()) {
                that.scroll_area();
            }
        });
        this.collapse_button.click(function () {
            that.expand();
        });
        this.collapse_button.hover(function () {
            $(this).addClass("ui-state-hover");
        }, function () {
            $(this).removeClass("ui-state-hover");
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
        };
    };


    OutputArea.prototype.expand = function () {
        if (this.collapsed) {
            this.collapse_button.hide();
            this.element.show();
            this.prompt_overlay.show();
            this.collapsed = false;
        };
    };


    OutputArea.prototype.toggle_output = function () {
        if (this.collapsed) {
            this.expand();
        } else {
            this.collapse();
        };
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


    OutputArea.prototype.scroll_if_long = function (lines) {
        if (this._should_scroll(lines)) {
            // only allow scrolling long-enough output
            this.scroll_area();
        };
    };


    OutputArea.prototype.toggle_scroll = function () {
        if (this.scrolled) {
            this.unscroll_area();
        } else {
            // only allow scrolling long-enough output
            this.scroll_if_long(20);
        };
    };


    // typeset with MathJax if MathJax is available
    OutputArea.prototype.typeset = function () {
        if (window.MathJax){
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
        }
    };


    OutputArea.prototype.handle_output = function (msg_type, content) {
        var json = {};
        json.output_type = msg_type;
        if (msg_type === "stream") {
            json.text = content.data;
            json.stream = content.name;
        } else if (msg_type === "display_data") {
            json = this.convert_mime_types(json, content.data);
        } else if (msg_type === "pyout") {
            json.prompt_number = content.execution_count;
            json = this.convert_mime_types(json, content.data);
        } else if (msg_type === "pyerr") {
            json.ename = content.ename;
            json.evalue = content.evalue;
            json.traceback = content.traceback;
        };
        // append with dynamic=true
        this.append_output(json, true);
    };


    OutputArea.prototype.convert_mime_types = function (json, data) {
        if (data['text/plain'] !== undefined) {
            json.text = data['text/plain'];
        };
        if (data['text/html'] !== undefined) {
            json.html = data['text/html'];
        };
        if (data['image/svg+xml'] !== undefined) {
            json.svg = data['image/svg+xml'];
        };
        if (data['image/png'] !== undefined) {
            json.png = data['image/png'];
        };
        if (data['image/jpeg'] !== undefined) {
            json.jpeg = data['image/jpeg'];
        };
        if (data['text/latex'] !== undefined) {
            json.latex = data['text/latex'];
        };
        if (data['application/json'] !== undefined) {
            json.json = data['application/json'];
        };
        if (data['application/javascript'] !== undefined) {
            json.javascript = data['application/javascript'];
        }
        return json;
    };


    OutputArea.prototype.append_output = function (json, dynamic) {
        // If dynamic is true, javascript output will be eval'd.
        this.expand();
        this.flush_clear_timeout();
        if (json.output_type === 'pyout') {
            this.append_pyout(json, dynamic);
        } else if (json.output_type === 'pyerr') {
            this.append_pyerr(json);
        } else if (json.output_type === 'display_data') {
            this.append_display_data(json, dynamic);
        } else if (json.output_type === 'stream') {
            this.append_stream(json);
        };
        this.outputs.push(json);
        var that = this;
        setTimeout(function(){that.element.trigger('resize');}, 100);
    };


    OutputArea.prototype.create_output_area = function () {
        var oa = $("<div/>").addClass("hbox output_area");
        if (this.prompt_area) {
            oa.append($('<div/>').addClass('prompt'));
        }
        return oa;
    };


    OutputArea.prototype.append_pyout = function (json, dynamic) {
        var n = json.prompt_number || ' ';
        var toinsert = this.create_output_area();
        if (this.prompt_area) {
            toinsert.find('div.prompt').addClass('output_prompt').html('Out[' + n + ']:');
        }
        this.append_mime_type(json, toinsert, dynamic);
        this.element.append(toinsert);
        // If we just output latex, typeset it.
        if ((json.latex !== undefined) || (json.html !== undefined)) {
            this.typeset();
        };
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
            this.append_text(s, toinsert);
            this.element.append(toinsert);
        };
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
        this.append_text(text, toinsert, "output_stream "+subclass);
        this.element.append(toinsert);
    };


    OutputArea.prototype.append_display_data = function (json, dynamic) {
        var toinsert = this.create_output_area();
        this.append_mime_type(json, toinsert, dynamic);
        this.element.append(toinsert);
        // If we just output latex, typeset it.
        if ( (json.latex !== undefined) || (json.html !== undefined) ) {
            this.typeset();
        };
    };


    OutputArea.prototype.append_mime_type = function (json, element, dynamic) {
        if (json.javascript !== undefined && dynamic) {
            this.append_javascript(json.javascript, element, dynamic);
        } else if (json.html !== undefined) {
            this.append_html(json.html, element);
        } else if (json.latex !== undefined) {
            this.append_latex(json.latex, element);
        } else if (json.svg !== undefined) {
            this.append_svg(json.svg, element);
        } else if (json.png !== undefined) {
            this.append_png(json.png, element);
        } else if (json.jpeg !== undefined) {
            this.append_jpeg(json.jpeg, element);
        } else if (json.text !== undefined) {
            this.append_text(json.text, element);
        };
    };


    OutputArea.prototype.append_html = function (html, element) {
        var toinsert = $("<div/>").addClass("box-flex1 output_subarea output_html rendered_html");
        toinsert.append(html);
        element.append(toinsert);
    };


    OutputArea.prototype.append_javascript = function (js, container) {
        // We just eval the JS code, element appears in the local scope.
        var element = $("<div/>").addClass("box-flex1 output_subarea");
        container.append(element);
        // Div for js shouldn't be drawn, as it will add empty height to the area.
        container.hide();
        // If the Javascript appends content to `element` that should be drawn, then
        // it must also call `container.show()`.
        try {
            eval(js);
        } catch(err) {
            console.log('Error in Javascript!');
            console.log(err);
            container.show();
            element.append($('<div/>')
                .html("Error in Javascript !<br/>"+
                    err.toString()+
                    '<br/>See your browser Javascript console for more details.')
                .addClass('js-error')
                );
        }
    }


    OutputArea.prototype.append_text = function (data, element, extra_class) {
        var toinsert = $("<div/>").addClass("box-flex1 output_subarea output_text");
        // escape ANSI & HTML specials in plaintext:
        data = utils.wrapUrls(data);
        data = utils.fixConsole(data);
        data = utils.fixCarriageReturn(data);
        data = utils.autoLinkUrls(data);
        if (extra_class){
            toinsert.addClass(extra_class);
        }
        toinsert.append($("<pre/>").html(data));
        element.append(toinsert);
    };


    OutputArea.prototype.append_svg = function (svg, element) {
        var toinsert = $("<div/>").addClass("box-flex1 output_subarea output_svg");
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
                return
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
    }


    OutputArea.prototype.append_png = function (png, element) {
        var toinsert = $("<div/>").addClass("box-flex1 output_subarea output_png");
        var img = $("<img/>").attr('src','data:image/png;base64,'+png);
        this._dblclick_to_reset_size(img);
        toinsert.append(img);
        element.append(toinsert);
    };


    OutputArea.prototype.append_jpeg = function (jpeg, element) {
        var toinsert = $("<div/>").addClass("box-flex1 output_subarea output_jpeg");
        var img = $("<img/>").attr('src','data:image/jpeg;base64,'+jpeg);
        this._dblclick_to_reset_size(img);
        toinsert.append(img);
        element.append(toinsert);
    };


    OutputArea.prototype.append_latex = function (latex, element) {
        // This method cannot do the typesetting because the latex first has to
        // be on the page.
        var toinsert = $("<div/>").addClass("box-flex1 output_subarea output_latex");
        toinsert.append(latex);
        element.append(toinsert);
    };


    OutputArea.prototype.handle_clear_output = function (content) {
        this.clear_output(content.stdout, content.stderr, content.other);
    }


    OutputArea.prototype.clear_output = function (stdout, stderr, other) {
        var that = this;
        if (this.clear_out_timeout != null){
            // fire previous pending clear *immediately*
            clearTimeout(this.clear_out_timeout);
            this.clear_out_timeout = null;
            this.clear_output_callback(this._clear_stdout, this._clear_stderr, this._clear_other);
        }
        // store flags for flushing the timeout
        this._clear_stdout = stdout;
        this._clear_stderr = stderr;
        this._clear_other = other;
        this.clear_out_timeout = setTimeout(function() {
            // really clear timeout only after a short delay
            // this reduces flicker in 'clear_output; print' cases
            that.clear_out_timeout = null;
            that._clear_stdout = that._clear_stderr = that._clear_other = null;
            that.clear_output_callback(stdout, stderr, other);
        }, 500
        );
    };


    OutputArea.prototype.clear_output_callback = function (stdout, stderr, other) {
        var output_div = this.element;

        if (stdout && stderr && other){
            // clear all, no need for logic
            output_div.html("");
            this.outputs = [];
            this.unscroll_area();
            return;
        }
        // remove html output
        // each output_subarea that has an identifying class is in an output_area
        // which is the element to be removed.
        if (stdout) {
            output_div.find("div.output_stdout").parent().remove();
        }
        if (stderr) {
            output_div.find("div.output_stderr").parent().remove();
        }
        if (other) {
            output_div.find("div.output_subarea").not("div.output_stderr").not("div.output_stdout").parent().remove();
        }
        this.unscroll_area();
        
        // remove cleared outputs from JSON list:
        for (var i = this.outputs.length - 1; i >= 0; i--) {
            var out = this.outputs[i];
            var output_type = out.output_type;
            if (output_type == "display_data" && other) {
                this.outputs.splice(i,1);
            } else if (output_type == "stream") {
                if (stdout && out.stream == "stdout") {
                    this.outputs.splice(i,1);
                } else if (stderr && out.stream == "stderr") {
                    this.outputs.splice(i,1);
                }
            }
        }
    };


    OutputArea.prototype.flush_clear_timeout = function() {
        var output_div = this.element;
        if (this.clear_out_timeout){
            clearTimeout(this.clear_out_timeout);
            this.clear_out_timeout = null;
            this.clear_output_callback(this._clear_stdout, this._clear_stderr, this._clear_other);
        };
    }


    // JSON serialization

    OutputArea.prototype.fromJSON = function (outputs) {
        var len = outputs.length;
        for (var i=0; i<len; i++) {
            // append with dynamic=false.
            this.append_output(outputs[i], false);
        };
    };


    OutputArea.prototype.toJSON = function () {
        var outputs = [];
        var len = this.outputs.length;
        for (var i=0; i<len; i++) {
            outputs[i] = this.outputs[i];
        };
        return outputs;
    };


    IPython.OutputArea = OutputArea;

    return IPython;

}(IPython));
