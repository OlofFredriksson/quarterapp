/*
 *
 * Copyright (c) 2013 Markus Eliasson, http://www.quarterapp.com/
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */
(function($) {
    "use strict";

    function Statistics(invoker, options) {
        this.options = $.extend({}, $.fn.category.defaults, options);
        this.init();
    }

    Statistics.prototype = {
        constructor : Statistics,

        init : function() {
            var ctxWeeks = $(".statistics-weeks").get(0).getContext("2d");
            var ctxMonths = $(".statistics-months").get(0).getContext("2d");
            var data = {
                labels : ["36","37","38","39","40","41","42","43","44","45"],
                datasets : [
                    {
                        fillColor : "rgba(151,187,205,0.5)",
                        strokeColor : "rgba(151,187,205,1)",
                        pointColor : "rgba(151,187,205,1)",
                        pointStrokeColor : "#fff",
                        data : [28,28,28,28,48,40,19,96,27,100]
                    }
                ]
            }
            var chartWeeks = new Chart(ctxWeeks).Line(data);
            var chartMonths = new Chart(ctxMonths).Line(data);

        }
    };

    // jQuery plugin definition
    $.fn.statistics = function(options) {
        var useOptions = {};
        if(options !== undefined) {
            useOptions = options;
        }

        return this.each(function(containerIndex) {
            var $this = $(this),
                data = $this.data('statistics');

            if(!data) {
                $this.data("statistics", (data = new Statistics($this, useOptions)));
                useOptions = {}; // Reset since we're in a loop
            }
        });
    };

    // Modal default configuration values
    $.fn.statistics.defaults = {

    };

    $.fn.statistics.Constructor = Statistics;

    // Automatically bind all existing modal invokers
    $(function() {
        $("body").statistics();
    }());
})(jQuery);