// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define(['base/js/utils'], function(utils) {
    "use strict";

    var FrameCommunicator = function (destination) {
        // Class used to communicate between browser frames.
        //
        // Parameters
        // ----------
        // destination: window
        //  Window that the communicator will talk with.
        this.destination = destination;

        // Callbacks by id
        this.callbacks = {};

        // Callback for message recieved.
        this.msg_callback = null; 

        // Register a message listener.
        var that = this;
        window.addEventListener('message', function(e){            
            // Check the message's source.  Only listen to messages from 
            // the destination frame.
            if (e.source != that._get_window(that.destination)) {
                return;
            }

            // TODO: Check e.origin

            that._handle_msg(e.data.id, e.data.data);
        });
    };
    
    FrameCommunicator.prototype.send = function(msg, callback, id) {
        // Sends a message to the destination frame.
        //
        // Parameters
        // ----------
        //  msg: jsonable
        //      Message contents
        //  callback: [callback=undefined]
        //      Called when a response is received.  Should have a signature of
        //      callback(msg, respond) (which is the same as the on_msg callback
        //      signature).
        //  id: [string=undefined]
        //      Used internally, allows the message id to be set when responding
        //      to a message from the destination.
        id = id || utils.uuid();
        if (callback) {
            this.callbacks[id] = callback;
        }

        // TODO: Set * to the known origin.
        var destination_window = this._get_window(this.destination);
        destination_window.postMessage({data: msg, id: id}, '*');
    };

    FrameCommunicator.prototype.on_msg = function(callback) {
        // Register a callback for message receiving.
        //
        // Parameters
        // ----------
        //  callback: callback
        //      Called when a message is recieved from the destination.  
        //      Callback should have the signature callback(msg, respond) where
        //      msg is the message contents, and respond is a function with the
        //      signature respond(msg, callback) (same as the send function),
        //      and allows you to send a message in response to the one recieved.
        this.msg_callback = callback;
    };

    FrameCommunicator.prototype._get_window = function(window_element) {
        // Gets the "window" of an element.
        var window_inst = window_element;
        if (window_inst[0] && window_inst[0].contentWindow) {
            window_inst = window_inst[0].contentWindow;
        }
        return window_inst;
    };

    FrameCommunicator.prototype._handle_msg = function(id, msg) {
        // Handles when a message is received.
        var that = this;
        var respond = function(response_msg, callback) {
            that.send(response_msg, callback, id);
        };

        // If a msg capturing callback is registered, call that instead of
        // calling the generic message handler.
        if (this.callbacks[id]) {
            this.callbacks[id](msg, respond);
            delete this.callbacks[id];
        } else if (this.msg_callback) {
            this.msg_callback(msg, respond);
        }
    };


    var HeightMonitor = function($el, callback) {
        // Watch an element and its children for height changes.
        //
        // Parameters
        // ----------
        //  $el: jquery element handle
        //  callback: callback
        //      Called when the height of the element changes.  Signature of
        //      callback(height).

        // Create an observer instance.
        this._height = -1;
        var that = this;
        this.observer = new MutationObserver(function(mutations) {
          mutations.forEach(function(mutation) {
            var height = $el.height();
            if (that._height != height) {
                that._height = height;
                callback(height);
            }
          });    
        });

        // Tell the observer to listen to the element and it's children.
        this.observer.observe($el[0],  { 
            attributes: true, 
            childList: true, 
            characterData: true, 
            subtree: true });
    };

    HeightMonitor.prototype.stop = function() {
        // Stop listening for height changes on the element.
        this.observer.disconnect();
    };
    
    return {
        'FrameCommunicator': FrameCommunicator,
        'HeightMonitor': HeightMonitor
    };
});
