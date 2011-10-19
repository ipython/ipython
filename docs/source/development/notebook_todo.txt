Notebook todo
=============

* Style the login page consistently with the rest of the site.
* Style the "Log Out" and username links in the header.
* Do a review of the header design and decide what to do about save widget moving
  to the Notebook section of the L panel.
* Show last saved time next to save widget.
* Make the header logo a link to "/".
* Add a better divider line between the header and the content area.
  - Fix spacing on notebook page.
* Organize templates to use inheritance and includes.

* Implement better restart logic.
  - Have LocalKernel monitor the hb port and always to restarts.
  - Have the WebSocket still monitor the hb and notify the user of restarts.

* Create unrendered rst cells.
* Users should be able to edit the contents of any cell in a global ACE editor.
* Add JSON'd metadata to the .py format notebooks.
* Implement white space between cells for insert. 
* Implement a notebook reload button.
* Indicate visual difference between html and markdown cell.
* Export should save first.
* Add ability to merge and split cells.
* Add Ctrl-Z for undo delete cell.
* Fix horizontal overflow and scrolling of output_area.
* Add per cells controls on the R side of each cell.
* Users should be able to drag a .py file to a cell and have it imported into that cell.

* Add reconnect logic in the javascript kernel.
* Add logic for failed ajax requests. With this, investigate returning JSON data to more
  completely describe the HTTP error codes.
* Test web services against hostile attacks.
* Add optional html sanitizing.
* Add timestamp to cells. ISO8601. IPython.utils.jsonutil.ISO8601. Save as 
  submitted/started/completed/received. See http://webcloud.se/log/JavaScript-and-ISO-8601/
* Try to figure out the issue with jQuery and <script> tags. See
  http://stackoverflow.com/questions/610995/jquery-cant-append-script-element

CodeMirror related
------------------

* Focus should only be called when the editor is on the page and visible.
* Refresh needs to be called when the editor is shown after hiding.
* Right now focus, then setValue causes the arrow keys to lock up. If that bug is
  not fixed, we need to possible move to passing the input to the CodeCell
  constructor.
* Implement a top-level refresh methods on Cells and the Notebook that can be called
  after page/notebook load.
* Make insert_code_cell_* methods not call select always. Probably move to a model
  where those methods take an options object.
* Notebook loading should be done without calls to select/focus/refresh. A single
  refresh pass should be done after everything has been made visible.
* Remove \u0000 from placeholders after the relevant CM bug is fixed.

