/*global Raphael:true*/
(function () {
    if (Raphael.vml) {
        Raphael.el.strokeLinearGradient = function () {
            // not supporting VML yet
            return this; // maintain chainability
        };
    } else {
        var setAttr = function (el, attr) {
            var key;
            if (attr) {
                for (key in attr) {
                    if (attr.hasOwnProperty(key)) {
                        el.setAttribute(key, attr[key]);
                    }
                }
            } else {
                return document.createElementNS("http://www.w3.org/2000/svg", el);
            }

            return null;
        };

        var defLinearGrad = function (defId, stops) {
            var def = setAttr("linearGradient");
            var i, l;
            def.id = defId;

            for (i = 0, l = stops.length; i < l; i += 1) {
                var stopEle = setAttr("stop");
                var stop = stops[i];
                setAttr(stopEle, stop);

                def.appendChild(stopEle);
            }

            return def;
        };

        Raphael.el.strokeLinearGradient = function (defId, width, stops) {

            if (stops) {
                this.paper.defs.appendChild(defLinearGrad(defId, stops));
            }

            setAttr(this.node, {
                "stroke": "url(#" + defId + ")",
                "stroke-width": width
            });

            return this; // maintain chainability
        };

        Raphael.st.strokeLinearGradient = function (defId, width, stops) {
            return this.forEach(function (el) {
                el.strokeLinearGradient(defId, width, stops);
            });
        };

        Raphael.fn.defineLinearGradient = function (defId, stops) {

            this.defs.appendChild(defLinearGrad(defId, stops));
        };
    }
}());

/*
 * ScaleRaphael 0.8 by Zevan Rosser 2010
 * For use with Raphael library : www.raphaeljs.com
 * Licensed under the MIT license.
 *
 * www.shapevent.com/scaleraphael/
 */
(function () {
    window.ScaleRaphael = function (container, width, height) {
        var wrapper = document.getElementById(container);
        if (!wrapper.style.position) wrapper.style.position = "relative";
        wrapper.style.width = width + "px";
        wrapper.style.height = height + "px";
        wrapper.style.overflow = "hidden";

        var nestedWrapper;

        if (Raphael.type == "VML") {
            wrapper.innerHTML = "<rvml:group style='position : absolute; width: 1000px; height: 1000px; top: 0px; left: 0px' coordsize='1000,1000' class='rvml' id='vmlgroup'><\/rvml:group>";
            nestedWrapper = document.getElementById("vmlgroup");
        } else {
            wrapper.innerHTML = "<div id='svggroup'><\/div>";
            nestedWrapper = document.getElementById("svggroup");
        }

        var paper = new Raphael(nestedWrapper, width, height);
        var vmlDiv;

        if (Raphael.type == "SVG") {
            paper.canvas.setAttribute("viewBox", "0 0 " + width + " " + height);
        } else {
            vmlDiv = wrapper.getElementsByTagName("div")[0];
        }

        paper.changeSize = function (w, h, center, clipping) {
            clipping = !clipping;

            var ratioW = w / width;
            var ratioH = h / height;
            var scale = ratioW < ratioH ? ratioW : ratioH;

            var newHeight = parseInt(height * scale);
            var newWidth = parseInt(width * scale);

            if (Raphael.type == "VML") {
                // scale the textpaths
                var txt = document.getElementsByTagName("textpath");
                for (var i in txt) {
                    var curr = txt[i];
                    if (curr.style) {
                        if (!curr._fontSize) {
                            var mod = curr.style.font.split("px");
                            curr._fontSize = parseInt(mod[0]);
                            curr._font = mod[1];
                        }
                        curr.style.font = curr._fontSize * scale + "px" + curr._font;
                    }
                }
                var newSize;
                if (newWidth < newHeight) {
                    newSize = newWidth * 1000 / width;
                } else {
                    newSize = newHeight * 1000 / height;
                }
                newSize = parseInt(newSize);
                nestedWrapper.style.width = newSize + "px";
                nestedWrapper.style.height = newSize + "px";
                if (clipping) {
                    nestedWrapper.style.left = parseInt((w - newWidth) / 2) + "px";
                    nestedWrapper.style.top = parseInt((h - newHeight) / 2) + "px";
                }
                vmlDiv.style.overflow = "visible";
            }

            if (clipping) {
                newWidth = w;
                newHeight = h;
            }

            wrapper.style.width = newWidth + "px";
            wrapper.style.height = newHeight + "px";
            paper.setSize(newWidth, newHeight);

            if (center) {
                wrapper.style.position = "absolute";
                wrapper.style.left = parseInt((w - newWidth) / 2) + "px";
                wrapper.style.top = parseInt((h - newHeight) / 2) + "px";
            }
        }

        paper.scaleAll = function (amount) {
            paper.changeSize(width * amount, height * amount);
        }

        paper.changeSize(width, height);

        paper.w = width;
        paper.h = height;

        return paper;
    }
})();