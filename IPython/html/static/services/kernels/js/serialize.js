// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'components/utf8/utf8'
    ], function ($, utf8) {
    "use strict";

    var _deserialize_binary = function(blob, callback) {
        // deserialize the binary message format
        // callback will be called with a message whose buffers attribute
        // will be an array of DataViews.
        var reader = new FileReader();
        reader.onload  = function () {
            var buf = this.result; // an ArrayBuffer
            var data = new DataView(buf);
            // read the header: 1 + nbufs 32b integers
            var nbufs = data.getInt32(0);
            var offsets = [];
            var i;
            for (i = 1; i <= nbufs; i++) {
                offsets.push(data.getInt32(i * 4));
            }
            // have to convert array to string for utf8.js
            var bytestring = String.fromCharCode.apply(null,
                new Uint8Array(buf.slice(offsets[0], offsets[1]))
            );
            var msg = $.parseJSON(
                utf8.decode(
                    bytestring
                )
            );
            // the remaining chunks are stored as DataViews in msg.buffers
            msg.buffers = [];
            var start, stop;
            for (i = 1; i < nbufs; i++) {
                start = offsets[i];
                stop = offsets[i+1] || buf.byteLength;
                msg.buffers.push(new DataView(buf.slice(start, stop)));
            }
            callback(msg);
        };
        reader.readAsArrayBuffer(blob);
    };

    var deserialize = function (data, callback) {
        // deserialize a message and pass the unpacked message object to callback
        if (typeof data === "string") {
            // text JSON message
            callback($.parseJSON(data));
        } else {
            // binary message
            _deserialize_binary(data, callback);
        }
    };
    
    return {
        deserialize : deserialize
    };
});