/** @odoo-module **/

import {COLORS} from "@web/views/graph/colors";
import {session} from "@web/session";

if (!session.company_chart_color_palette) return;

const darken = (hexColor, magnitude) => {
    hexColor = hexColor.replace(`#`, ``);
    if (hexColor.length === 6) {
        const decimalColor = parseInt(hexColor, 16);
        let r = (decimalColor >> 16) + magnitude;
        r > 255 && (r = 255);
        r < 0 && (r = 0);
        let g = (decimalColor & 0x0000ff) + magnitude;
        g > 255 && (g = 255);
        g < 0 && (g = 0);
        let b = ((decimalColor >> 8) & 0x00ff) + magnitude;
        b > 255 && (b = 255);
        b < 0 && (b = 0);
        return `#${(g | (b << 8) | (r << 16)).toString(16)}`;
    } else {
        return hexColor;
    }
};


let rainBow = ["#6E40AA", "#6054C8", "#4C6EDB", "#368CE1", "#23ABD8", "#1AC7C2", "#1DDFA3", "#30EF82", "#52F667", "#7FF658", "#AFF05B", "#C6D63C", "#E2B72F", "#FB9633", "#FF7847", "#FF5E63", "#FE4B83", "#E4419D", "#BF3CAF", "#963DB3"]
let cool = ["#25E892", "#1FE29D", "#1CDCA8", "#1AD4B2", "#19CDBC", "#1AC4C5", "#1DBBCD", "#20B2D4", "#25A8DA", "#2B9EDE", "#3194E0", "#388AE1", "#3F80E1", "#4676DF", "#4D6DDB", "#5464D6", "#5B5CCF", "#6154C7", "#664DBE", "#6A46B4"]
let RdYlBu = ["#C5E5EF", "#D5EDEF", "#E2F3E8", "#EEF8DB", "#F6F9CB", "#FBF6BA", "#FEF0AA", "#FEE59B", "#FED98B", "#FDCA7C", "#FDB96E", "#FBA761", "#F99456", "#F57F4B", "#F06B42", "#E85639", "#DE4331", "#D3312B", "#C52028", "#B51026"]
let spectral = ["#F0704A", "#F5814E", "#F99456", "#FBA65F", "#FDB76A", "#FDC676", "#FED483", "#FEE191", "#FEEB9F", "#FDF3AA", "#FBF8B0", "#F6FAAE", "#EEF8A8", "#E4F4A2", "#D7EF9F", "#C8E99F", "#B6E2A1", "#A3DAA3", "#8FD2A4", "#7CC8A6"]
let YlGn = ["#EFF9B6", "#E7F6AE", "#DEF2A8", "#D3EDA1", "#C7E89B", "#BAE294", "#ACDC8E", "#9DD688", "#8DCF81", "#7DC87A", "#6DC073", "#5DB86B", "#4EAF63", "#41A65B", "#369B53", "#2C904C", "#228645", "#187C40", "#0F733C", "#086A38"]
let RdPu = ["#5D006F", "#6F0174", "#830178", "#96027B", "#A90880", "#BC1386", "#CD248E", "#DC3796", "#E74B9B", "#F05FA0", "#F673A6", "#F887AC", "#FA9AB3", "#FBABB8", "#FBBABE", "#FCC6C5", "#FCD2CE", "#FCD2CE", "#FEE5E2", "#FEEEEB"]

let colors = {
    "default": {
        "name": "Odoo Default",
        "colors": COLORS
    },
    "palette_1": {
        "name": "Odoo Stars",
        "colors": ["#7cb5ec", "#434348", "#90ed7d", "#f7a35c", "#8085e9", "#f15c80", "#e4d354", "#2b908f", "#f45b5b", "#91e8e1", "#2f7ed8", "#0d233a", "#8bbc21", "#910000", "#1aadce", "#492970", "#f28f43", "#77a1e5", "#c42525", "#a6c96a"]
    },
    "palette_2": {
        "name": "Happy",
        "colors": ['#98EECC', '#B799FF', '#F6BA6F', '#EA8FEA', '#386cb0', '#FF55BB', '#DC8449', '#5BC0F8', '#CDE990', '#FFF6BD', '#A555EC', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#006837', '#B01E68', "#8bd3c7", "#eeb8b0", "#c7c8ca"]
    },
    "palette_3": {
        "name": "Pastel",
        "colors": ['#fbb4ae', '#b3cde3', '#ccebc5', '#decbe4', '#fed9a6', '#ffffcc', '#e5d8bd', '#fddaec', '#f2f2f2', '#b3e2cd', '#fdcdac', '#cbd5e8', '#f4cae4', '#e6f5c9', '#fff2ae', '#f1e2cc', '#cccccc', "#66c2a5", "#fc8d62", "#8da0cb"]
    },
    "palette_4": {
        "name": "Spring",
        "colors": ["#FF0075", "#77D970", "#4421af", "#1a53ff", "#0d88e6", "#00b7c7", "#C32BAD", "#28FFBF", "#ebdc78", "#fd7f6f", "#7eb0d5", "#b2e061", "#bd7ebe", "#ffb55a", "#ffee65", "#beb9db", "#fdcce5", "#8bd3c7", "#eeb8b0", "#c7c8ca"]
    },
    "palette_5": {
        "name": "Winter",
        "colors": ['#4E79A7', '#A0CBE8', '#F28E2B', '#FFBE7D', '#59A14F', '#8CD17D', '#B6992D', '#F1CE63', '#499894', '#86BCB6', '#E15759', '#FF9D9A', '#79706E', '#BAB0AC', '#D37295', '#FABFD2', '#B07AA1', '#D4A6C8', '#9D7660', '#D7B5A6']
    },
    "palette_6": {
        "name": "Neon",
        "colors": ['#7149C6', '#FC2947', '#2CD3E1', '#B3FFAE', '#FF55BB', '#F5EA5A', '#332FD0', '#d5bb21', '#30AADD', '#FEB139', '#f06719', '#14C38E', '#F806CC', '#fc719e', '#E3FCBF', '#C70A80', '#a26dc2', '#E15FED', '#FBFF00', "#28FFBF"]
    },
    "palette_7": {
        "name": "Retro Metro",
        "colors": ["#ea5545", "#f46a9b", "#dc0ab4", "#ef9b20", "#9b19f5", "#edbf33", "#00bbb4", "#50e991", "#ede15b", "#e60049", "#e6d800", "#bdcf32", "#87bc45", "#27aeef", "#ffa300", "#b3d4ff", "#00bfa0", "#b33dc6", "#fd7f6f", "#abadda"]
    },
    "palette_8": {
        "name": "Apple iMac",
        "colors": ["#25476d", "#10505b", "#b72c31", "#c7c8ca", "#d48207", "#e36942", "#353a71", "#a8bed2", "#a4beb2", "#eeb8b0", "#c7c8ca", "#eaca96", "#e9aa95", "#abacca", "#ffa300", "#b3d4ff", "#00bfa0", "#b33dc6", "#fd7f6f", "#abadda"]
    },
    "palette_9": {
        "name": "Dracula",
        "colors": ["#282a36", "#5C5470", "#476D7C", "#6272a4", "#1D267D", "#116D6E", "#C74B50", "#F73D93", "#7A0BC0", "#950101", "#700B97", "#5C3D2E", "#6E85B2", "#492970", '#616F39', '#C060A1', '#0D7377', '#B5076B', '#9D7660', '#FFC045']
    },
    "palette_10": {
        "name": "Rainbow",
        "colors": rainBow
    },
    "palette_11": {
        "name": "Cool",
        "colors": cool
    },
    "palette_12": {
        "name": "Red Yellow Blue",
        "colors": RdYlBu
    },
    "palette_13": {
        "name": "Spectral",
        "colors": spectral
    },
    "palette_14": {
        "name": "Yellow & Green",
        "colors": YlGn
    },
    "palette_15": {
        "name": "Red & Purple",
        "colors": RdPu
    }
}


let selected_colors = colors[session.company_chart_color_palette].colors;
for (var i in selected_colors) {
    if (session.user_theme_mode && session.user_theme_mode === "dark-mode") {
        COLORS[i] = darken(selected_colors[i], -50);

    } else {
        COLORS[i] = selected_colors[i];
    }
}