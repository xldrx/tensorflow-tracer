let tooltips = document.getElementsByClassName("bk-tooltip");

for (var i = 0, len = tooltips.length; i < len; i ++) {
    let el = tooltips[i];
    el.style.zIndex = "1002";
    let viewportOffset = el.getBoundingClientRect();
    let left = viewportOffset.left;
    let right = viewportOffset.right;
    let width = (window.innerWidth || document.documentElement.clientWidth);
    width -= 20;
    let current_left = parseFloat(tooltips[i].style.left);
    if (left < 0) {
     tooltips[i].style.left = (current_left - left) + "px";
    } else if (right >= width) {
     tooltips[i].style.left = (current_left - right + width ) + "px";
    }
}