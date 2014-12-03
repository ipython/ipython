// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'underscore',
    ], function (_) {
    "use strict";
    
    var _deserialize_array_buffer = function (buf) {
        var data = new DataView(buf);
        // read the header: 1 + nbufs 32b integers
        var nbufs = data.getUint32(0);
        var offsets = [];
        var i;
        for (i = 1; i <= nbufs; i++) {
            offsets.push(data.getUint32(i * 4));
        }
        var json_bytes = new Uint8Array(buf.slice(offsets[0], offsets[1]));
        var msg = JSON.parse(
            (new TextDecoder('utf8')).decode(json_bytes)
        );
        // the remaining chunks are stored as DataViews in msg.buffers
        msg.buffers = [];
        var start, stop;
        for (i = 1; i < nbufs; i++) {
            start = offsets[i];
            stop = offsets[i+1] || buf.byteLength;
            msg.buffers.push(new DataView(buf.slice(start, stop)));
        }
        return msg;
    };
    
    var _deserialize_binary = function(data, callback) {
        /**
         * deserialize the binary message format
         * callback will be called with a message whose buffers attribute
         * will be an array of DataViews.
         */
        if (data instanceof Blob) {
            // data is Blob, have to deserialize from ArrayBuffer in reader callback
            var reader = new FileReader();
            reader.onload = function () {
                var msg = _deserialize_array_buffer(this.result);
                callback(msg);
            };
            reader.readAsArrayBuffer(data);
        } else {
            // data is ArrayBuffer, can deserialize directly
            var msg = _deserialize_array_buffer(data);
            callback(msg);
        }
    };

    var deserialize = function (data, callback) {
        /**
         * deserialize a message and pass the unpacked message object to callback
         */
        if (typeof data === "string") {
            // text JSON message
            callback(JSON.parse(data));
        } else {
            // binary message
            _deserialize_binary(data, callback);
        }
    };
    
    var _serialize_binary = function (msg) {
        /**
         * implement the binary serialization protocol
         * serializes JSON message to ArrayBuffer
         */
        msg = _.clone(msg);
        var offsets = [];
        var buffers = [];
        msg.buffers.map(function (buf) {
            buffers.push(buf);
        });
        delete msg.buffers;
        var json_utf8 = (new TextEncoder('utf8')).encode(JSON.stringify(msg));
        buffers.unshift(json_utf8);
        var nbufs = buffers.length;
        offsets.push(4 * (nbufs + 1));
        var i;
        for (i = 0; i + 1 < buffers.length; i++) {
            offsets.push(offsets[offsets.length-1] + buffers[i].byteLength);
        }
        var msg_buf = new Uint8Array(
            offsets[offsets.length-1] + buffers[buffers.length-1].byteLength
        );
        // use DataView.setUint32 for network byte-order
        var view = new DataView(msg_buf.buffer);
        // write nbufs to first 4 bytes
        view.setUint32(0, nbufs);
        // write offsets to next 4 * nbufs bytes
        for (i = 0; i < offsets.length; i++) {
            view.setUint32(4 * (i+1), offsets[i]);
        }
        // write all the buffers at their respective offsets
        for (i = 0; i < buffers.length; i++) {
            msg_buf.set(new Uint8Array(buffers[i].buffer), offsets[i]);
        }
        
        // return raw ArrayBuffer
        return msg_buf.buffer;
    };
    
    var serialize = function (msg) {
        if (msg.buffers && msg.buffers.length) {
            return _serialize_binary(msg);
        } else {
            return JSON.stringify(msg);
        }
    };
    
    var exports = {
        deserialize : deserialize,
        serialize: serialize
    };
    return exports;
});