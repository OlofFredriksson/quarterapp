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

    function Timesheet(invoker, options) {
        this.options = $.extend({}, $.fn.category.defaults, options);
        this.current_activity = { "id": -1, "color" : "#fff", "title" : "Idle"};
        this.summary_markup = '<tr data-activity-id="{0}" style="color: {1};"><td class="sheettime-value">{2}</td><td class="sheettime-name">{3}</td></tr>';
        this.pending_update = 0;
        this.current_date = undefined;
        this.$overlay = $("#modal-overlay");
        this.$comment_modal = $("#comment-modal");
        this.$comment_invoker = jQuery();
        this.init();
    }

    Timesheet.prototype = {
        constructor : Timesheet,

        init : function() {
            $(".activity-row").on("click", $.proxy(this.on_select_activity, this));

            // Only render work hours
            $("table.sheet tr").slice(0, 6).hide();
            $("table.sheet tr").slice(18, 24).hide();
            $("#extend-sod").on("click", $.proxy(this.on_extend_sod, this));
            $("#extend-eod").on("click", $.proxy(this.on_extend_eod, this));

            // Sheet marker event
            $("table.sheet td").bind("mousedown", $.proxy(this.on_sheet_mouse_down, this));
            $("table.sheet td").bind("mousemove", $.proxy(this.on_sheet_mouse_move, this));
            $("body").bind("mouseup", $.proxy(this.on_sheet_mouse_up, this));

            // Quarter comment
            $("table.sheet td span").bind("dblclick", $.proxy(this.on_show_quarter_comment, this));

            // Date selector
            if($("#datepicker").length > 0) {
                var current_date = $("#sheet").attr("data-sheet-date");
                this.current_date = new Date(current_date);
                var picker = new Pikaday({
                    field: document.getElementById('datepicker'),
                    firstDay : 1,
                    defaultDate : this.current_date,
                    setDefaultDate : true,
                    onSelect: $.proxy(this.on_select_date, this)
                });
            }

            // Set the current activity
            var activity = this.get_preferred_activity();
            this.set_current_activity(activity);

            this.show_sheets_activities();
        },

        /**
         * Load a new page when the user selects a different date in the sheet view
         */
        on_select_date : function(date) {
            if((date.getFullYear() === this.current_date.getFullYear()) &&
                (date.getMonth() === this.current_date.getMonth()) &&
                (date.getDate() === this.current_date.getDate())) {
                return;
            }

            var location = "/application/timesheet/" + quarterapp.to_date_string(date);
            window.location = location;
        },

        /**
         * Extend the sheet view with an hour at the start of day (if possible)
         */
        on_extend_sod : function() {
            var $rows = $("table.sheet tbody tr").slice(0, 11);
            for(var i = $rows.length-1; i > -1; i--) {
                if(! $rows.eq(i).is(":visible") ) {
                    $rows.eq(i).show();
                    return;
                }
            }
        },

        /**
         * Extend the sheet view with an hour at the end of day (if possible)
         */
        on_extend_eod : function() {
            var $rows = $("table.sheet tbody tr").slice(12, 24);
            for(var i = 0; i < $rows.length; i++) {
                if(! $rows.eq(i).is(":visible") ) {
                    $rows.eq(i).show();
                    return;
                }
            }
        },

        on_select_activity : function(event) {
            var $element = $(event.target)
                .closest(".activity-row");

            var new_id = $element.attr("data-activity-id"),
                new_color = $element.attr("data-activity-color"),
                new_title = $element.attr("data-activity-title");

            var activity = { "id": new_id, "color" : new_color, "title" : new_title };
            this.set_current_activity(activity);
        },

        /**
         * Setup the activity update "transaction". Nothing will be sent to the server until the
         * mouse is relased and all updated activities are sent at once.
         */
        on_sheet_mouse_down : function(event) {
            if(event.which !== 1) {
                return;
            }

            this.pending_update = event.timeStamp;
        },

        /**
         * Update activity cell if mouse is pressed, keep original values in case of update error.
         * This function does not communicate with the server, all pending updates are accumalated
         * and transmitted at mouse up.
         */
        on_sheet_mouse_move : function(event) {
            if(event.which !== 1) {
                return;
            }

            if(this.pending_update == 0 || ((event.timeStamp - this.pending_update) < 200)) {
                return;
            }

            this.paint_cell($(event.target));
        },

        /**
         * Finalize the activity update by issueing an update request to the server. We expect that
         * all goes well (as we already updated UI and state), but if it failes restore to old activities
         * again.
         */
        on_sheet_mouse_up : function(event) {
            function cleanup_pending_activities() {
                var $activities = $("table.sheet span.activity-cell.pending");
                // Remove any temporary attributes
                $activities.removeAttr("data-activity-previous-id");
                $activities.removeAttr("data-activity-previous-color");

                // Remove all pending states
                $activities.removeClass("pending");
            }

            if(event.which !== 1) {
                return;
            }

            if(this.pending_update == 0) {
                return;
            }

            var self = this,
                $activities = $("table.sheet span.activity-cell.pending");

            if($activities.length > 0) {
                var indexes = []
                $.each($activities, function(index, cell) {
                    indexes.push($(cell).attr("data-activity-index"));
                });
                
                indexes = indexes + ""

                $.ajax({
                    url : "/api/sheet/" + quarterapp.to_date_string(self.current_date),
                    type : "PUT",
                    data : {
                        "indexes" : indexes,
                        "activity" : self.current_activity.id,
                    },
                    success : function(data, status, jqXHR) {
                        var summary_total = $("#summary-hours"),
                            summary_table = $("#sheet-summary");
                        summary_total.html(new Number(data.total).toFixed(2));
                        summary_table.empty();
                        summary_table.append("<tbody></tbody>");
                        $.each(data.summary, function(index, act) {
                            var ac = self.summary_markup.format(act.id, act.color, new Number(act.sum).toFixed(2), act.title);
                            summary_table.append(ac);
                        });
                    },
                    error : function(jqXHR, status, errorThrown) {
                    }
                });    
            }

            cleanup_pending_activities();
            this.pending_update = 0;
        },

        on_show_quarter_comment : function(event) {
            var self = this;

            if($(event.target).hasClass("activity-cell")) {
                this.$comment_invoker = $(event.target);
            }
            else {
                this.$comment_invoker = $(event.target).parents(".activity-cell");
            }
            

            var quarter_id = this.$comment_invoker.attr("data-quarter-id");
            if(quarter_id != undefined && quarter_id != -1) {

                $.ajax({
                    url : "/api/comment/" + quarter_id,
                    success : function(data, status, jqXHR) {
                        if(data != undefined) {
                            $("#comment").val(data.comment);
                        }
                    },
                    error : function(jqXHR, status, errorThrown) {
                        $("#comment").attr("disabled", "disabled");
                        self.$comment_modal.find(".message").addClass("negative").html("Could not retrieve comment!");
                        self.$comment_modal.find("form").attr("disabled", "disabled");
                    }
                });

                this.$comment_modal.addClass("show");
                this.$overlay.addClass("show");

                this.$overlay.on("click", $.proxy(this.on_comment_close, this));
                this.$comment_modal.find(".button.close").on("click", $.proxy(this.on_comment_close, this));
                this.$comment_modal.find("form").on("submit", $.proxy(this.on_comment_submit, this));

                return false;
            }
        },

        on_comment_close : function() {
            event.preventDefault();

            this.$comment_modal.removeClass("show");
            this.$overlay.removeClass("show");
            this.$comment_modal.find("form").off("submit");
            this.$overlay.off("click");
            this.$comment_modal.find(".button.close").off("click");

            this.$comment_invoker = jQuery();
        },

        on_comment_submit : function(event) {
            var self = this,
                quarter_id = this.$comment_invoker.attr("data-quarter-id"),
                comment = this.$comment_modal.find("textarea").val();

            event.preventDefault();

            $.ajax({
                url : "/api/comment/" + quarter_id,
                type : "PUT",
                data : {
                    "comment" : comment
                },
                success : function(data, status, jqXHR) {
                    // TODO: Update span with icon
                    self.on_comment_close();
                },
                error : function(jqXHR, status, errorThrown) {
                    self.$comment_modal.find(".message").addClass("negative").html("<span class='icon error'>&nbsp;</span>Could not save comment!");
                }
            });

            return false;
        },

        set_current_activity : function(activity) {
            $(".activity-list").find(".current-activity").removeClass("current-activity");
            $(".activity-list").find("[data-activity-id='" + activity.id + "']").find(".icon").addClass("current-activity");
            this.current_activity = activity;
            this.set_preferred_activity(activity);
        },

        /**
         * Set the preferred activity to use in the sheet view.
         */
        set_preferred_activity : function(activity) {
            if(typeof(localStorage) != "undefined") {
                localStorage.setItem("quarter-activity-id", activity.id);
                localStorage.setItem("quarter-activity-title", activity.title);
                localStorage.setItem("quarter-activity-color", activity.color);
            }
        },

        /**
         * Get the preferred activity to use as the default activity on the sheet view.
         */
        get_preferred_activity : function() {
            if(typeof(localStorage) != "undefined") {
                return { "id" :  localStorage.getItem("quarter-activity-id"),
                         "title" : localStorage.getItem("quarter-activity-title"),
                         "color" : localStorage.getItem("quarter-activity-color") };
            }
            else {
                return this.current_activity;
            }
        },

        /**
         * In sheet view, show all activities that are used, even if they are before
         * or after start-of-day or end-of-day limit.
         */
        show_sheets_activities : function() {
            var $early_rows = $("table.sheet tbody tr").slice(0, 11),
                $late_rows = $("table.sheet tbody tr").slice(12, 24),
                found_it = false;

            var process_row = function() {
                if(found_it === true) {
                    $current_row.show();
                    return true;
                }
                else if(! $current_row.is(":visible") ) {
                    if($current_row.find("span[data-activity-id!='-1']").length > 0) {
                        $current_row.show();
                        return true;
                    }
                }
            };

            // Go through early rows from start, if one row contains used activity. 
            // Show that row, and all subsequent early rows
            for(var i = 0; i < $early_rows.length; i++) {
                var $current_row = $early_rows.eq(i);
                found_it = process_row($current_row, found_it);
            }

            found_it = false;

            // Go through late rows from the end, if one row contains a used activity.
            // Show that row and all subsequent rows.
            for(var i = $late_rows.length-1; i > -1; i--) {
                var $current_row = $late_rows.eq(i);
                found_it = process_row($current_row, found_it);
            }
        },

        paint_cell : function($activity_cell) {
            var activity_id = $activity_cell.attr("data-activity-id");

            if(activity_id === undefined) {
                return; // Not an activity cell, just ignore.
            }

            // Cell is already updated, just ignore.
            // (this is safe since we only allow one update at a time, it is's painted, it's painted)
            if($activity_cell.attr("data-activity-previous-id") !== undefined) {
                return;
            }

            // Store the old activity id and old color for the activity
            // these will be reused if the update does not succeed.
            $activity_cell.attr("data-activity-previous-id", activity_id);
            $activity_cell.attr("data-activity-previous-color", $activity_cell.css("background-color"));

            // Set new id
            $activity_cell.attr("data-activity-id", this.current_activity.id);

            // Update cells background color and border to new activities color
            $activity_cell.css("background-color", this.current_activity.color);
            $activity_cell.css("border-color", quarterapp.luminance(this.current_activity.color, -0.2));

            // Add pending state class (used for visual feedback)
            $activity_cell.addClass("pending");
        }
    };

    // jQuery plugin definition
    $.fn.timesheet = function(options) {
        var useOptions = {};
        if(options !== undefined) {
            useOptions = options;
        }

        return this.each(function() {
            var $this = $(this),
                data = $this.data('timesheet');

            if(!data) {
                $this.data("timesheet", (data = new Timesheet($this, useOptions)));
                useOptions = {}; // Reset since we're in a loop
            }
        });
    };

    // Modal default configuration values
    $.fn.timesheet.defaults = {

    };

    $.fn.timesheet.Constructor = Timesheet;

    // Automatically bind all existing modal invokers
    $(function() {
        $("body").timesheet();
    }());
})(jQuery);