//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Kernel Status Popup using webkit notification API
//
// This is an example of widget binding to the hooks broadcasting the
//
// Status of the kernel to pop up a notification when the kernel has been busy
// for more than a certain time, and become idle again
//
// Notification out of the browser are possible thanks to the Webkit
// notifcation Api, that for now is implemented only on chrome.
//============================================================================

//============================================================================
// This need the Webkit Notification Extension for IPython to work
//============================================================================


var IPython = (function (IPython) {

    var utils = IPython.utils;

    var WebkitKernelNotifier = function () {
        this.last_busy_time=new Date().getTime();
        this.was_busy=false;
        var that=this;
        // method of object need to be connected to the hook hub by wrapping
        // them in closure
        $(IPython.hook).bind("kernel_busy",function(){that.status_busy()});
        $(IPython.hook).bind("kernel_idle",function(){that.status_idle()});
    }


    WebkitKernelNotifier.prototype.status_busy = function () {
        this.last_busy_time=new Date().getTime();
        this.was_busy=true;
    };


    WebkitKernelNotifier.prototype.status_idle = function () {
        now = new Date().getTime();
        dt=(now-this.last_busy_time)

        // TODO: Put it in a timer and trigger only if not re-busy in the next
        // second
        if (this.was_busy && dt  > 1000 )
        {
            IPython.notifier.Notify('',
                'Kernel Idle',
                'kernel was busy for around '+Math.ceil(dt/1000)+' seconds' 
                )
        }
        this.was_busy=false;
    };

    IPython.WebkitKernelNotifier = WebkitKernelNotifier;
    return IPython;

}(IPython));

// This doesn't need any UI interface, so we can instanciate it as soon as
// IPython.hook exist
IPython.chrome_kernel_notifier = new IPython.WebkitKernelNotifier();

