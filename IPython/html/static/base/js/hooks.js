//----------------------------------------------------------------------------
//  Copyright (C) 2014  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Hook
//============================================================================

/**
 * A Hook is a sequence of callbacks. They are called in order based on their
 * nice values (lower nice values are executed first).
 *
 * @module IPython
 * @namespace IPython
 */

var IPython = (function(IPython) {
    "use strict";

    /**
     * @class Hook
     * @constructor
     */
    var Hook = function() {
        this.items = [];
    };


    /**
     * Add a callback to the hook.
     *
     * @method add_callback
     * @param {function} callback - The callback to be added to the hook.
     * @param {number} [nice=0] - Optional number representing the callback priority.
     *        The lower the number, the higher the priority is.
     * @return {function} - The added callback.
     */
    Hook.prototype.add_callback = function(callback, nice) {
        nice = nice == null ? 0 : nice;
        var item = {callback: callback, nice: nice};
        var i = this.items.length;
        while (i > 0 && nice < this.items[i - 1].nice) i--;
        this.items.splice(i, 0, item);
        return callback;
    };


    /**
     * Remove a callback from the hook.
     *
     * @method remove_callback
     * @param {function} callback - The callback to be removed.
     */
    Hook.prototype.remove_callback = function(callback) {
        var l = this.items.length;
        for (var i = 0; i < l; i++) {
            if (this.items[i].callback === callback) {
                this.items.splice(i, 1);
                return;
            }
        }
    };


     /**
     * Execute the hook callbacks.
     *
     * @method execute
     * @param {Array} args - An array of data. Its elements will be passed as arguments to the callbacks.
     */
    Hook.prototype.execute = function(args) {
        var l = this.items.length;
        for (var i = 0;  i < l; i++)
            this.items[i].callback.apply(window, args);
    }

    IPython.Hook = Hook;

    return IPython;

}(IPython));

