console.log(me);
let start = me.x_range.start;
let end = me.x_range.end;
console.log(start, end);

for (var model_id in me.document._all_models) {
    model = me.document._all_models[model_id];
    if (model.type === "Plot") {
        console.log(model);
        console.log(model.x_range);
        //model.x_range.set('start', start);
        //model.x_range.set('end', end);
        model.x_range.start = start;
        model.x_range.end = end;
    }
    if (model.type === "Button") {
        model.disabled = true;
        if (model.label === " Sync") {
            model.css_classes = ['xl-hidden'];
        }
    }

}