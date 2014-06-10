Used https://github.com/jdfreder/bootstrap2to3 to migrate the Notebook to Bootstrap 3.

Additional changes:
- Set `.tab-content .row` `0px;` left and right margin (bootstrap default is `-15px;`)  
- Removed `height: @btn_mini_height;` from `.list_header>div, .list_item>div` in `tree.less`  
- Set `#header` div `margin-bottom: 0px;`
- Set `#menus` to `float: left;`
- Set `#maintoolbar .navbar-text` to `float: none;`

- Added no-padding convienence class.
- Set border of #maintoolbar to 0px