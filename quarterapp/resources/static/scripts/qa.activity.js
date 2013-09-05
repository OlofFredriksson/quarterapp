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

    function Activity(invoker, options) {
        this.options = $.extend({}, $.fn.activity.defaults, options);
        this.$invoker = $(invoker);
        this.$overlay = $("#modal-overlay");
        this.$modal = $("#activity-modal");
        this.activity_action = this.$invoker.attr("data-activity-action"); 
        this.activity_bar_markup = '<div class="activity-bar"><div class="activity-palette" style="background-color: {3};"></div><div class="activity-details"><div class="activity-title">{2}</div><div class="quarter-count">Using <span class="count">0</span> quarters</div></div><a href="#" class="icon medium edit" data-activity-action="edit" data-activity-id="{1}" data-category-id="{0}">&nbsp;</a></div>';
        this.activity_disabled_bar_markup = '<div class="activity-bar disabled"><div class="activity-palette" style="background-color: {3};"></div><div class="activity-details"><div class="activity-title">{2}</div><div class="quarter-count">Using <span class="count">0</span> quarters</div></div><a href="#" class="icon medium edit" data-activity-action="edit" data-activity-id="{1}" data-category-id="{0}">&nbsp;</a><span class="disabled"></span></div>';
        this.init();
    }

    Activity.prototype = {
        constructor : Activity,

        init : function() {
            this.$invoker.on("click", $.proxy(this.on_action, this));
        },

        on_action : function() {
            var self = this;
            if(this.activity_action === "edit") {
                $("#activity-modal").find("h2").html("Edit activity");
                var activity_id = this.$invoker.attr("data-activity-id");
                this.update_field_values(activity_id);

                this.$modal.find(".button.delete").show();
                this.$modal.find(".button.delete").on("click", $.proxy(this.on_delete, this));
            }
            else {
                this.$modal.find(".button.delete").hide();
            }
            this.$modal.addClass("show");
            this.$overlay.addClass("show");

            this.$overlay.on("click", $.proxy(this.on_close, this));
            this.$modal.find(".button.close").on("click", $.proxy(this.on_close, this));

            self.$modal.find("form").on("submit", $.proxy(this.on_submit, this));

            return false;
        },

        on_close : function(event) {
            event.preventDefault();

            this.$modal.removeClass("show");
            this.$overlay.removeClass("show");
            this.$modal.find("form").off("submit");
            this.$overlay.off("click");
            this.$modal.find(".button.close").off("click");
            this.$modal.find(".button.delete").off("click");

            this.restore_modal();

            return false;
        },

        on_submit : function(event) {
            var self = this,
                category_id = this.$invoker.attr("data-category-id"),
                title = this.$modal.find("input.title").val(),
                color = this.$modal.find("input.color").val(),
                enabled = this.$modal.find(".input.switcher").hasClass("on");

            event.preventDefault();

            if(this.activity_action === "edit") {
                var activity_id = this.$invoker.attr("data-activity-id");
                this.update_activity(activity_id, category_id, title, color, enabled);
            }
            else {
                this.create_activity(category_id, title, color, enabled);
            }

            return false;
        },

        on_delete : function(event) {
            var self = this,
                activity_id = this.$invoker.attr("data-activity-id");

            event.preventDefault();

            $.ajax({
                url : "/api/activity/" + activity_id,
                type : "DELETE",
                success : function(data, status, jqXHR) {
                    self.$invoker.parents(".activity-bar").remove();
                    self.on_close();
                },
                error : function(jqXHR, status, errorThrown) {
                    self.$modal.find(".message").addClass("negative").html("<span class='icon error'>&nbsp;</span>Could not delete activity!");
                }
            });
            return false;
        },

        restore_modal : function() {
            var $title = this.$modal.find("input.title"),
                $color = this.$modal.find("input.color");

            $title.val("");
            $title.removeClass("error");
            $title.siblings("div.input-error").remove();
            
            $color.val("#fff");
            $color.css("background-color", "#fff");
            $color.css("color", "#fff");
            $color.removeClass("error");
            $color.siblings("div.input-error").remove();
            
            this.$modal.find(".message").html("");

            this.$modal.find(".input.switcher").removeClass("off").addClass("on");
        },

        update_field_values : function(activity_id) {
            var self = this;
            
            if(activity_id != undefined) {
                $.ajax({
                    url : "/api/activity/" + activity_id,
                    success : function(data, status, jqXHR) {
                        self.$modal.find("input.title").val(data.title);
                        self.$modal.find("input.color").val(data.color);
                        self.$modal.find("input.color")
                            .css("background-color", data.color)
                            .css("color", data.color);

                        if(data.enabled) {
                            self.$modal.find(".input.switcher").removeClass("off").addClass("on");
                        }
                        else {
                            self.$modal.find(".input.switcher").removeClass("on").addClass("off");
                        }
                        
                        self.$modal.find("form").on("submit", $.proxy(this.on_submit, this));
                        
                    },
                    error : function(jqXHR, status, errorThrown) {
                        $("#category-title").attr("disabled", "disabled");
                        self.$modal.find(".message").addClass("negative").html("<span class='icon error'>&nbsp;</span>Could not retrieve activity details!");
                        self.$modal.find("form").attr("disabled", "disabled");
                    }
                });
            }   
        },

        create_activity : function(category_id, title, color, enabled) {
            var self = this;
            $.ajax({
                url : "/api/activity",
                type : "POST",
                data : {
                    "category" : category_id,
                    "title" : title,
                    "color" : color,
                    "enabled" : enabled
                },
                success : function(data, status, jqXHR) {
                    self.add_activity_bar(data);
                    $("body").trigger("ajax");
                    self.on_close();
                },
                error : function(jqXHR, status, errorThrown) {
                    self.$modal.find(".message").addClass("negative").html("<span class='icon error'>&nbsp;</span>Could not create activity!");
                }
            });
        },

        update_activity : function(activity_id, category_id, title, color, enabled) {
            var self = this;
            $.ajax({
                url : "/api/activity/" + activity_id,
                type : "PUT",
                data : {
                    "category" : category_id,
                    "title" : title,
                    "color" : color,
                    "enabled" : enabled
                },
                success : function(data, status, jqXHR) {
                    self.$invoker.siblings(".activity-palette").css("background-color", data.color);
                    self.$invoker.siblings(".activity-details").find(".activity-title").html(data.title);

                    self.$invoker.parents(".activity-bar").removeClass("disabled")
                    if(!data.enabled) {
                        self.$invoker.parents(".activity-bar").addClass("disabled")
                    }
                    $("body").trigger("ajax");
                    self.on_close();
                },
                error : function(jqXHR, status, errorThrown) {
                    self.$modal.find(".message").addClass("negative").html("<span class='icon error'>&nbsp;</span>Could not update activity!");
                }
            });
        },

        add_activity_bar : function(activity) {
            var $list = $("section.group[data-category-id='" + activity.category + "']").find(".content");
            if(activity.enabled) {
                $list.append(this.activity_bar_markup.format(activity.category, activity.id, activity.title, activity.color));    
            }
            else {
                $list.append(this.activity_disabled_bar_markup.format(activity.category, activity.id, activity.title, activity.color));    
            }
        }
    };

    // jQuery plugin definition
    $.fn.activity = function(options) {
        var useOptions = {};
        if(options !== undefined) {
            useOptions = options;
        }

        return this.each(function(containerIndex) {
            var $this = $(this),
                data = $this.data('activity');

            if(!data) {
                $this.data("activity", (data = new Activity($this, useOptions)));
                useOptions = {}; // Reset since we're in a loop
            }
        });
    };

    // Modal default configuration values
    $.fn.activity.defaults = {
    };

    $.fn.activity.Constructor = Activity;

    // Check additional bindings after ajax
    $("body").on("ajax", function() {
        $("a[data-activity-action]").activity();    
    });

    // Automatically bind all existing modal invokers
    $(function() {
        $("a[data-activity-action]").activity();
    }());
})(jQuery);