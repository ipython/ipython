$(function () {

    module("bootstrap-tooltip")

      test("should provide no conflict", function () {
        var tooltip = $.fn.tooltip.noConflict()
        ok(!$.fn.tooltip, 'tooltip was set back to undefined (org value)')
        $.fn.tooltip = tooltip
      })

      test("should be defined on jquery object", function () {
        var div = $("<div></div>")
        ok(div.tooltip, 'popover method is defined')
      })

      test("should return element", function () {
        var div = $("<div></div>")
        ok(div.tooltip() == div, 'document.body returned')
      })

      test("should expose default settings", function () {
        ok(!!$.fn.tooltip.defaults, 'defaults is defined')
      })

      test("should empty title attribute", function () {
        var tooltip = $('<a href="#" rel="tooltip" title="Another tooltip"></a>').tooltip()
        ok(tooltip.attr('title') === '', 'title attribute was emptied')
      })

      test("should add data attribute for referencing original title", function () {
        var tooltip = $('<a href="#" rel="tooltip" title="Another tooltip"></a>').tooltip()
        equals(tooltip.attr('data-original-title'), 'Another tooltip', 'original title preserved in data attribute')
      })

      test("should place tooltips relative to placement option", function () {
        $.support.transition = false
        var tooltip = $('<a href="#" rel="tooltip" title="Another tooltip"></a>')
          .appendTo('#qunit-fixture')
          .tooltip({placement: 'bottom'})
          .tooltip('show')

        ok($(".tooltip").is('.fade.bottom.in'), 'has correct classes applied')
        tooltip.tooltip('hide')
      })

      test("should allow html entities", function () {
        $.support.transition = false
        var tooltip = $('<a href="#" rel="tooltip" title="<b>@fat</b>"></a>')
          .appendTo('#qunit-fixture')
          .tooltip({html: true})
          .tooltip('show')

        ok($('.tooltip b').length, 'b tag was inserted')
        tooltip.tooltip('hide')
        ok(!$(".tooltip").length, 'tooltip removed')
      })

      test("should respect custom classes", function () {
        var tooltip = $('<a href="#" rel="tooltip" title="Another tooltip"></a>')
          .appendTo('#qunit-fixture')
          .tooltip({ template: '<div class="tooltip some-class"><div class="tooltip-arrow"/><div class="tooltip-inner"/></div>'})
          .tooltip('show')

        ok($('.tooltip').hasClass('some-class'), 'custom class is present')
        tooltip.tooltip('hide')
        ok(!$(".tooltip").length, 'tooltip removed')
      })

      test("should fire show event", function () {
        stop()
        var tooltip = $('<div title="tooltip title"></div>')
          .bind("show", function() {
            ok(true, "show was called")
            start()
          })
          .tooltip('show')
      })

      test("should fire shown event", function () {
        stop()
        var tooltip = $('<div title="tooltip title"></div>')
          .bind("shown", function() {
            ok(true, "shown was called")
            start()
          })
          .tooltip('show')
      })

      test("should not fire shown event when default prevented", function () {
        stop()
        var tooltip = $('<div title="tooltip title"></div>')
          .bind("show", function(e) {
            e.preventDefault()
            ok(true, "show was called")
            start()
          })
          .bind("shown", function() {
            ok(false, "shown was called")
          })
          .tooltip('show')
      })

      test("should fire hide event", function () {
        stop()
        var tooltip = $('<div title="tooltip title"></div>')
          .bind("shown", function() {
            $(this).tooltip('hide')
          })
          .bind("hide", function() {
            ok(true, "hide was called")
            start()
          })
          .tooltip('show')
      })

      test("should fire hidden event", function () {
        stop()
        var tooltip = $('<div title="tooltip title"></div>')
          .bind("shown", function() {
            $(this).tooltip('hide')
          })
          .bind("hidden", function() {
            ok(true, "hidden was called")
            start()
          })
          .tooltip('show')
      })

      test("should not fire hidden event when default prevented", function () {
        stop()
        var tooltip = $('<div title="tooltip title"></div>')
          .bind("shown", function() {
            $(this).tooltip('hide')
          })
          .bind("hide", function(e) {
            e.preventDefault()
            ok(true, "hide was called")
            start()
          })
          .bind("hidden", function() {
            ok(false, "hidden was called")
          })
          .tooltip('show')
      })

      test("should not show tooltip if leave event occurs before delay expires", function () {
        var tooltip = $('<a href="#" rel="tooltip" title="Another tooltip"></a>')
          .appendTo('#qunit-fixture')
          .tooltip({ delay: 200 })

        stop()

        tooltip.trigger('mouseenter')

        setTimeout(function () {
          ok(!$(".tooltip").is('.fade.in'), 'tooltip is not faded in')
          tooltip.trigger('mouseout')
          setTimeout(function () {
            ok(!$(".tooltip").is('.fade.in'), 'tooltip is not faded in')
            start()
          }, 200)
        }, 100)
      })

      test("should not show tooltip if leave event occurs before delay expires, even if hide delay is 0", function () {
        var tooltip = $('<a href="#" rel="tooltip" title="Another tooltip"></a>')
          .appendTo('#qunit-fixture')
          .tooltip({ delay: { show: 200, hide: 0} })

        stop()

        tooltip.trigger('mouseenter')

        setTimeout(function () {
          ok(!$(".tooltip").is('.fade.in'), 'tooltip is not faded in')
          tooltip.trigger('mouseout')
          setTimeout(function () {
            ok(!$(".tooltip").is('.fade.in'), 'tooltip is not faded in')
            start()
          }, 200)
        }, 100)
      })

      test("should not show tooltip if leave event occurs before delay expires", function () {
        var tooltip = $('<a href="#" rel="tooltip" title="Another tooltip"></a>')
          .appendTo('#qunit-fixture')
          .tooltip({ delay: 100 })
        stop()
        tooltip.trigger('mouseenter')
        setTimeout(function () {
          ok(!$(".tooltip").is('.fade.in'), 'tooltip is not faded in')
          tooltip.trigger('mouseout')
          setTimeout(function () {
            ok(!$(".tooltip").is('.fade.in'), 'tooltip is not faded in')
            start()
          }, 100)
        }, 50)
      })

      test("should show tooltip if leave event hasn't occured before delay expires", function () {
        var tooltip = $('<a href="#" rel="tooltip" title="Another tooltip"></a>')
          .appendTo('#qunit-fixture')
          .tooltip({ delay: 150 })
        stop()
        tooltip.trigger('mouseenter')
        setTimeout(function () {
          ok(!$(".tooltip").is('.fade.in'), 'tooltip is not faded in')
        }, 100)
        setTimeout(function () {
          ok($(".tooltip").is('.fade.in'), 'tooltip has faded in')
          start()
        }, 200)
      })

      test("should destroy tooltip", function () {
        var tooltip = $('<div/>').tooltip().on('click.foo', function(){})
        ok(tooltip.data('tooltip'), 'tooltip has data')
        ok($._data(tooltip[0], 'events').mouseover && $._data(tooltip[0], 'events').mouseout, 'tooltip has hover event')
        ok($._data(tooltip[0], 'events').click[0].namespace == 'foo', 'tooltip has extra click.foo event')
        tooltip.tooltip('show')
        tooltip.tooltip('destroy')
        ok(!tooltip.hasClass('in'), 'tooltip is hidden')
        ok(!$._data(tooltip[0], 'tooltip'), 'tooltip does not have data')
        ok($._data(tooltip[0], 'events').click[0].namespace == 'foo', 'tooltip still has click.foo')
        ok(!$._data(tooltip[0], 'events').mouseover && !$._data(tooltip[0], 'events').mouseout, 'tooltip does not have any events')
      })

      test("should show tooltip with delegate selector on click", function () {
        var div = $('<div><a href="#" rel="tooltip" title="Another tooltip"></a></div>')
        var tooltip = div.appendTo('#qunit-fixture')
                         .tooltip({ selector: 'a[rel=tooltip]',
                                    trigger: 'click' })
        div.find('a').trigger('click')
        ok($(".tooltip").is('.fade.in'), 'tooltip is faded in')
      })

      test("should show tooltip when toggle is called", function () {
        var tooltip = $('<a href="#" rel="tooltip" title="tooltip on toggle"></a>')
          .appendTo('#qunit-fixture')
          .tooltip({trigger: 'manual'})
          .tooltip('toggle')
        ok($(".tooltip").is('.fade.in'), 'tooltip should be toggled in')
      })

      test("should place tooltips inside the body", function () {
        var tooltip = $('<a href="#" rel="tooltip" title="Another tooltip"></a>')
          .appendTo('#qunit-fixture')
          .tooltip({container:'body'})
          .tooltip('show')
        ok($("body > .tooltip").length, 'inside the body')
        ok(!$("#qunit-fixture > .tooltip").length, 'not found in parent')
        tooltip.tooltip('hide')
      })

      test("should place tooltip inside window", function(){
        var container = $("<div />").appendTo("body")
            .css({position: "absolute", width: 200, height: 200, bottom: 0, left: 0})
          , tooltip = $("<a href='#' title='Very very very very very very very very long tooltip'>Hover me</a>")
          .css({position: "absolute", top:0, left: 0})
          .appendTo(container)
          .tooltip({placement: "top", animate: false})
          .tooltip("show")

        stop()

        setTimeout(function(){
          ok($(".tooltip").offset().left >= 0)

          start()
          container.remove()
        }, 100)
      })

      test("should place tooltip on top of element", function(){
        var container = $("<div />").appendTo("body")
              .css({position: "absolute", bottom: 0, left: 0, textAlign: "right", width: 300, height: 300})
            , p = $("<p style='margin-top:200px' />").appendTo(container)
            , tooltiped = $("<a href='#' title='very very very very very very very long tooltip'>Hover me</a>")
              .css({marginTop: 200})
              .appendTo(p)
              .tooltip({placement: "top", animate: false})
              .tooltip("show")

        stop()

        setTimeout(function(){
          var tooltip = container.find(".tooltip")

          start()
          ok(tooltip.offset().top + tooltip.outerHeight() <= tooltiped.offset().top)
          container.remove()
        }, 100)
      })
})
