* Added a widget persistence API.  This allows you to persist your notebooks interactive widgets.
  Two levels of control are provided:
  1. Higher level- ``WidgetManager.set_state_callbacks`` allows you to register callbacks for loading and saving widget state.  The callbacks you register are automatically called when necessary.
  2. Lower level- the ``WidgetManager`` Javascript class now has ``get_state`` and ``set_state`` methods that allow you to get and set the state of the widget runtime.

  Example code for persisting your widget state to session data:
  
  ::
    %%javascript
    require(['widgets/js/manager'], function(manager) {
        manager.WidgetManager.set_state_callbacks(function() { // Load
            return JSON.parse(sessionStorage.widgets_state || '{}');
        }, function(state) { // Save
            sessionStorage.widgets_state = JSON.stringify(state);
        });
    });