import os
from continuumweb import hemlib
from tornado import web

def notebook_render(view, notebook_id):
    app = view.application.ipython_app
    template = view.application.jinja2_env.get_template('notebook.html')
    nbm = view.application.notebook_manager
    project = nbm.notebook_dir_for_id(notebook_id)
    if not nbm.notebook_exists(notebook_id):
        raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
    view.write( template.render(
        project=project,
        notebook_id=notebook_id,
        base_project_url=app.base_project_url,
        base_kernel_url=app.base_kernel_url,
        kill_kernel=False,
        read_only=view.read_only,
        logged_in=view.logged_in,
        login_available=view.login_available,
        mathjax_url=app.mathjax_url,
        use_less=view.use_less,
        js_scripts = make_hem_scripts(app.assets_domain, app.compress_assets)))

def make_hem_scripts(asset_url, compress_assets):
    #desired functionality - logging, homedirs, unixusername, database
    #basedir is the directory of the current file
    _basedir = os.path.abspath(os.path.dirname(__file__))
    hemlib.slug_path = _basedir
    if compress_assets:
        return [asset_url + "js/ipynb_application.js"]
    else:
        js_files = hemlib.slug_json()['libs']
        #hack "static/" off the beginning of each js file
        corrected = [j[7:] for j in js_files]
        static_js = hemlib.django_slug_libs(
            _basedir,
            asset_url,
            corrected)
        
        return static_js
