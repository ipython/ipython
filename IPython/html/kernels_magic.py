"""
Kernel's magic work in progress
"""
import os
from IPython.display import display, Javascript, HTML

list = """<div id='kernels_list'>
     List of Active Kernels:
    <ul>
    
    </ul>
</div>
"""

nb = """<div class="list_item row-fluid">
    <div class="span12">
        <i class="item_icon icon-book"></i>
        <a class="item_link" href="/notebooks/" target="_blank">
        <span class="item_name">kernels magic.ipynb</span></a>
        <div class="item_buttons btn-group pull-right">
            <button class="btn btn-mini btn-danger">Shutdown</button>
        </div>
    </div>
</div>"""

# TODO: refactor notebooklist.js so the relevant portion we've ripped out here
# can be used from a util function.
js = """
var nb = '<div class="list_item row-fluid"> <div class="span12"> <i class="item_icon icon-book"></i> <a class="item_link" href="/notebooks/NAME" target="_blank"> <span class="item_name">NAME</span></a> <div class="item_buttons btn-group pull-right"> <button class="btn btn-mini btn-danger">Shutdown</button> </div> </div> </div>'

var load_sessions = function () {
    var settings = {
        processData : false,
        cache : false,
        type : "GET",
        dataType : "json",
        success : $.proxy(function(d) { 
            console.log(d);
            for (var i = d.length-1; i >= 0; i--) {
                var c = d[i];
                console.log(c.id);
                // 
                var x = $('#kernels_list ul').append(nb.replace(/NAME/g, c.notebook.name));
                add_shutdown_button(x, c.id);
                //$('#kernels_list ul').append("<li>" + c.notebook.name + "</li>")
                //$('#kernels_list ul').append("<button class='btn btn-mini btn-danger'>Shutdown</button>")
            }
        }, this)
    };
    var url = utils.url_join_encode('/api/sessions');
    var aj= $.ajax(url,settings);
};

load_sessions();

// TODO: this was ripped out of notebooklist.js, refactor to use it
var add_shutdown_button = function (item, session) {
        var that = this;
        console.log('adding ', item, session);
        var shutdown_button = $("<button/>").text("Shutdown").addClass("btn btn-mini btn-danger").
            click(function (e) {
                var settings = {
                    processData : false,
                    cache : false,
                    type : "DELETE",
                    dataType : "json",
                    success : function () {
                        that.load_sessions();
                    }
                };
                var url = utils.url_join_encode(
                    '/',
                    'api/sessions',
                    session
                );
                $.ajax(url, settings);
                return false;
            });
        // var new_buttons = item.find('a'); // shutdown_button;
        item.find(".input_button").text("").append(shutdown_button);
    
    
        console.log(shutdown_button);
        item.find('.item_buttons').text("").append(shutdown_button);
    
    };
"""
def list_kernels(line=''):
    display(HTML(list))
    display(Javascript(js))

def load_ipython_extension(ip):
    ip.magics_manager.register_function(list_kernels, magic_name='kernels')
    list_kernels()
