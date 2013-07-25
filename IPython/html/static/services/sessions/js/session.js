//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Notebook
//============================================================================

var IPython = (function (IPython) {
    
    var Session = function(notebook_path, Notebook){
        this.kernel = null;
        this.kernel_id = null;
        this.session_id = null;
        this.notebook_path = notebook_path;
        this.notebook = Notebook;
        this._baseProjectUrl = Notebook.baseProjectUrl() 
    };
    
    Session.prototype.start = function(){
        var that = this
        var qs = $.param({notebook_path:this.notebook_path});
        var url = '/api/sessions' + '?' + qs;
        $.post(url, 
            $.proxy(this.start_kernel, that),
            'json'
        );
    };
    
    Session.prototype.notebook_rename = function (notebook_path) {
        this.notebook_path = notebook_path;
        var settings = {
            processData : false,
            cache : false,
            type : "PATCH",
            data: notebook_path,
            dataType : "json",
        };
        var url = this._baseProjectUrl + 'api/sessions/' + this.session_id;
        $.ajax(url, settings);
    }
    
    
    Session.prototype.delete_session = function() {
        var settings = {
            processData : false,
            cache : false,
            type : "DELETE",
            dataType : "json",
        };
        var url = this._baseProjectUrl + 'api/sessions/' + this.session_id;
        $.ajax(url, settings);
    };
    
    // Kernel related things
    /**
     * Start a new kernel and set it on each code cell.
     * 
     * @method start_kernel
     */
    Session.prototype.start_kernel = function (json) {
        this.session_id = json.id;
        this.kernel_content = json.kernel;
        var base_url = $('body').data('baseKernelUrl') + "api/kernels";
        this.kernel = new IPython.Kernel(base_url, this.session_id);
        // Now that the kernel has been created, tell the CodeCells about it.
        this.kernel._kernel_started(this.kernel_content);
    };
    
    /**
     * Prompt the user to restart the IPython kernel.
     * 
     * @method restart_kernel
     */
    Session.prototype.restart_kernel = function () {
        this.kernel.restart();
    };
    
    Session.prototype.interrupt_kernel = function() {
        this.kernel.interrupt();
    };
    

    Session.prototype.kill_kernel = function() {
        this.kernel.kill();        
    };
    
    IPython.Session = Session;


    return IPython;

}(IPython));
