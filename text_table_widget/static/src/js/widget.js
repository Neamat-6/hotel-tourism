odoo.define('text_table_widget.TextTableWidget', function(require) { "use strict";

    var field_registry = require('web.field_registry');
    var fields = require('web.basic_fields');

    var FieldTextTableWidget = fields.FieldChar.extend({
        template: 'FieldTextTableWidget',

        events: {
            'click .ik-button-text-table': 'button_action_clik',
        },

        button_action_clik: function(event) {

            var raw_data = event.target.outerHTML
            var data = this.decode_data(raw_data);

            if(data.model){
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: data.model,
                    views: [[false, 'form']],
                    target: 'new',
                    context:data.context,
                    res_id: data.id,
                });
            }
        },

        encode_data: function(val){
            var data = "###+"+JSON.stringify(val)+"-###";
            return data.replaceAll('"', '@')
        },
        decode_data: function(raw_data){
            if(!raw_data.includes("###+")){
                return {}
            }
            var data = raw_data.substring( raw_data.indexOf("###+") + 4, raw_data.lastIndexOf("-###") );
            return JSON.parse(data.replaceAll('@', '"'))
        },


        generate_html: function(value) {
            try {var data = JSON.parse(value);} catch(e) {console.log(e);var data = [];}
            var screen_data = data['data'];
            var body = ""

            if(data.styles){
                body += `<style>${data.styles}</style>`
            }

            body += "<table>"
            for(var x in screen_data) {

                body += "<tr>"
                var row = screen_data[x]
                for(var y in row) {
                    var col = row[y]
                    var content = ""

                    var col_width = col.col_width || "100%"

                    if(col.type == "button_action"){
                        var parameters = this.encode_data({model:col.model, id: col.res_id, context: col.context})
                        var btn_class = col.class
                        if(!btn_class){btn_class="btn-link"}
                        btn_class += "\tik-button-text-table"
                        var button_icon = "";if(col.icon){button_icon = `<i class="fa ${col.icon} fa-2x" />`};
                        var button_name = col.name || "";
                        if(button_icon){
                            button_name = `<span style="font-size:9px;float:right;">${button_name}</span>`
                        }
                        var content = `<button data-id="${parameters}" class="${btn_class}">${button_icon}${button_name}</button>`
                    }

                    if(col.type == "col_head"){
                        var head_name = col.name || "";

                        var icon = "";if(col.icon){icon = `<i class="fa ${col.icon} fa-2x" />`};
                        var content = `<button style="border-radius: 0; padding-top: 4px; font-weight: bold; border: 0; height: 44px; width: 100%; background: #afafaf; ">${icon}${head_name}</button>`
                    }

                    if(col.type == "row_head"){
                        var head_name = col.name || "";
                        var content = `<button style="border-radius: 0; padding-top: 4px; height: 44px; width: 100%; background: white; border: 1px solid #afafaf; color: black; ">${head_name}</button>`
                    }

                    body += `<td class="text-nowrap" style="width:${col_width}">${content}</td>`
                }
                body += "</tr>"
            }
            body += "</table>"

            return body
        },

        _renderReadonly: function () {
            var html_value = ""

            if(this.value){
                var html_value = this.generate_html(this.value)
            }else{
                html_value = "<h2>Not Loaded ...</h2>"
            }


            this.$el.find('.table-content').html(html_value);
        },

    });

    field_registry
        .add('text_table', FieldTextTableWidget);

return {
    FieldTextTableWidget: FieldTextTableWidget
};

});