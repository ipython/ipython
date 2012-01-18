//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//=====================================================//
// Webkit Notification Extension for webkit, based on 
// http://0xfe.blogspot.com/2010/04/desktop-notifications-with-webkit.html
//
// This in mainly convenient method to activate/send notification to 
// the webkit Notification Api, only availlable on chrome for
// now. This doesn't **do** anything by itself, but is used 
// generate the UI element to activate/deactivate notification.
// It is then used by other js plugins to show notification
//=====================================================//

var IPython = (function (IPython) {
    function Notifier() {
        this._enabled=false;
    }

    Notifier.prototype.enable = function(bool) {
        this._enabled=bool;
    }

    // Does the browser support notification
    Notifier.prototype.HasSupport = function() {
      if (window.webkitNotifications) {
          console.log('Checking support for notification...Yes !');
          return true;
      } else {
          console.log('Checking support for notification...No.');
          return false;
      }
    }

    // Request permission for this page to send notifications. If allowed,
    // calls function "cb" with "true" as the first argument.
    //================================================
    // This function to reques permission of showing notification have to be
    // triggerd on user action.  Otherwise it is **ignored** by the browser so
    // don't just request permission at startup, but when user check `enable
    // notification`
    //================================================
    Notifier.prototype.RequestPermission = function(cb) {
      console.log('Requesting permission to show webkit notification..');
      window.webkitNotifications.requestPermission(
      function() {
        if (cb) { cb(window.webkitNotifications.checkPermission() == 0); }
        }
      );
    }

    // Popup a notification with icon, title, and body. Returns false if
    // permission was not granted.
    Notifier.prototype.Notify = function(icon, title, body) {
      if (window.webkitNotifications.checkPermission() == 0 && this._enabled) {
        var popup = window.webkitNotifications.createNotification(
          icon, title, body);
        popup.show();
        return true;
      }

      return false;
    }

    IPython.Notifier = Notifier; 
    notifier = new Notifier();

    // If browser does not have support don't do anythings
    if (!notifier.HasSupport()) {
        return IPython;
    }

    //================================================
    // Create a checkbox in the config section
    //================================================
    config = $('div#config_section');
    ccl= config.children().last();
    ccl2=$('<div>').addClass('section_row ui-helper-clearfix');
    ccl.append(ccl2);
    ccl2.append($('<span/>').addClass('section_row_buttons').html('<input type="checkbox" id="enable_notification" checked="true" title="Enable Notification">'));
    ccl2.append(
        $('<span/>').addClass('section_row_buttons').html(
            '<span class="checkbox_label" id="" title="">Enable webkit notification:</span>'
            )
    );

    
    that=this;
    $("#enable_notification").attr('checked',false);
    //==========================================================
    // Request permission **have to** be triggerd on user action
    //==========================================================
    $("#enable_notification").click(function() {
        var state = $('#enable_notification').prop('checked');
        notifier.RequestPermission();
        notifier.enable(state);
    });

    IPython.notifier = notifier;
    return IPython;
}(IPython));
