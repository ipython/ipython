"""
Kernel's magic work in progress
"""
from IPython.display import display, Javascript, HTML

list = """
        <div class="item_buttons btn-group">
            <button id="refresh_kernels" class="btn btn-mini">Active Kernels (click to update)</button>
        </div>
        <div class="alert" style="margin: 10px">
        Warning: Opening a notebook from here that is still open in another
        browser window may cause unpredictable state.
        </div>
<div id='kernels_list'></div>
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

var this_path = IPython.notebook.notebook_path + "/" + IPython.notebook.notebook_name;
var load_sessions = function () {
    var settings = {
        processData : false,
        cache : false,
        type : "GET",
        dataType : "json",
        success : $.proxy(function(d) { 
            // clear out the previous list
            $('#kernels_list').replaceWith("<div id='kernels_list'></div>")
            for (var i = d.length-1; i >= 0; i--) {
                var path = d[i].notebook.path + '/' + d[i].notebook.name;
                var x = $('#kernels_list').append(nb.replace(/NAME/g, path));
                if (path == this_path) {
                    x.find('.list_item').slice(-1).find('a')
                        .removeAttr('href').attr('title', 'this notebook');
                }
                add_shutdown_button(x, d[i].id);
            }
        }, this)
    };
    var url = utils.url_join_encode('/api/sessions');
    var aj= $.ajax(url,settings);
};

load_sessions();

$('#refresh_kernels').click(load_sessions);

// TODO: this was ripped out of notebooklist.js, refactor to use it
var add_shutdown_button = function (item, session) {
        var shutdown_button = $("<button/>").text("Shutdown").addClass("btn btn-mini btn-danger").
            click(function (e) {
                var settings = {
                    processData : false,
                    cache : false,
                    type : "DELETE",
                    dataType : "json",
                    success : function () {
                        load_sessions();
                    }
                };
                var url = utils.url_join_encode(
                    IPython.notebook.base_url,
                    'api/sessions',
                    session
                );
                $.ajax(url, settings);
                return false;
            });
        item.find('.item_buttons').text("").append(shutdown_button);
    
    };
"""
def list_kernels(line=''):
    """
    List the notebooks with the currently active kernels. You can shutdown
    these kernels by clicking the red "Shutdown" button.

    TODO: add `%kernels kill kernel_id` option
    """
    display(HTML(list))
    display(Javascript(js))

def load_ipython_extension(ip):
    ip.magics_manager.register_function(list_kernels, magic_name='kernels')
