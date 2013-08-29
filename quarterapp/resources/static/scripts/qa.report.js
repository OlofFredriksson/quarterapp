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

    function Report(invoker, options) {
        this.options = $.extend({}, $.fn.category.defaults, options);
        this.init();
    }

    Report.prototype = {
        constructor : Report,

        init : function() {
            // Bind the date selectors
            var self = this;
            $("input.datepicker").each(function(index, element) {
                var picker = new Pikaday({
                    field: element,
                    firstDay : 1,
                    setDefaultDate : true,
                    format : "YYYY-MM-DD"
                });
            });            
        }
    };

    // jQuery plugin definition
    $.fn.report = function(options) {
        var useOptions = {};
        if(options !== undefined) {
            useOptions = options;
        }

        return this.each(function(containerIndex) {
            var $this = $(this),
                data = $this.data('report');

            if(!data) {
                $this.data("report", (data = new Report($this, useOptions)));
                useOptions = {}; // Reset since we're in a loop
            }
        });
    };

    // Modal default configuration values
    $.fn.report.defaults = {

    };

    $.fn.report.Constructor = Report;

    // Automatically bind all existing modal invokers
    $(function() {
        $("body").report();
    }());
})(jQuery);