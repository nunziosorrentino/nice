var monthNames = ["Jan", "Feb", "Mar", "Ap", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

function startTime() {
    var today = new Date();
    var utc_y = today.getUTCFullYear()
    var utc_m = today.getUTCMonth()
    var utc_d = today.getUTCDate()
    var utc_hh = today.getUTCHours()

    //local
    var h = today.getHours() //getHours();
    var d = today.getDate();
    var h = today.getHours();
    var m = today.getMinutes();
    var s = today.getSeconds();

    var tt = today.getTime()

    m = checkTime(m);
    s = checkTime(s);
    document.getElementById('timeclock').innerHTML =
    utc_d +" "+monthNames[utc_m]+ " " +utc_y+ " "+utc_hh + ":" + m + ":" + s + " UTC<br>"+
    d + " " + monthNames[utc_m]+ " " + utc_y+" "+h + ":" + m + ":" + s + " Local time<br>"+
    unix2gps(Math.round(1e-3*tt))+ " GPS time<br><br>";

    var t = setTimeout(startTime, 500);
}

function checkTime(i) {
    if (i < 10) {i = "0" + i};  // add zero in front of numbers < 10
    return i;
}


/*
    gpstimeutil.js: a javascript library which translates between GPS and unix time

    Copyright (C) 2012  Jeffery Kline

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see &lt;http://www.gnu.org/licenses/&gt;.

*/

/*
Javascript code is based on original at:
  http://www.andrews.edu/~tzs/timeconv/timealgorithm.html

The difference between the original and this version is that this
  version handles the leap seconds using linear interpolation, not a
  discontinuity.  Linear interpolation guarantees a 1-1 correspondence
  between gps times and unix times.

  By contrast, for example, the original implementation maps both gps
  times 46828800.5 and 46828800 map to unix time 362793599.5


Following may be helpful for conversion when new leap seconds are
announced.

gnu 'date':

  date --date='2012-06-30 23:59:59' +%s

Mac OSX 'date':

  date -j -f '%Y-%m-%d %H:%M:%S' '2012-06-30 23:59:60' +%s
*/


function getleaps() {
    'use strict';
    return [46828800, 78364801, 109900802, 173059203, 252028804,
            315187205, 346723206, 393984007, 425520008, 457056009, 504489610,
            551750411, 599184012, 820108813, 914803214, 1025136015, 1119744016,
            1341118800, 1167264017];
}

// Test to see if a GPS second is a leap second
function isleap(gpsTime) {
    'use strict';

    var i, isLeap, leaps;
    isLeap = false;
    leaps = getleaps();
    for (i = 0; i < leaps.length; i += 1) {
        if (gpsTime === leaps[i]) {
            isLeap = true;
            break;
        }
    }
    return isLeap;
}

// Count number of leap seconds that have passed
function countleaps(gpsTime, accum_leaps) {
    'use strict';

    var i, leaps, nleaps;
    leaps = getleaps();
    nleaps = 0;

    if (accum_leaps) {
        for (i = 0; i < leaps.length; i += 1) {
            if (gpsTime + i >= leaps[i]) {
                nleaps += 1;
            }
        }
    } else {
        for (i = 0; i < leaps.length; i += 1) {
            if (gpsTime >= leaps[i]) {
                nleaps += 1;
            }
        }
    }
    return nleaps;
}


// Test to see if a unixtime second is a leap second
function isunixtimeleap(unixTime) {
    'use strict';

    var gpsTime;
    gpsTime = unixTime - 315964800;
    gpsTime += countleaps(gpsTime, true) - 1;

    return isleap(gpsTime);
}


// Convert Unix Time to GPS Time
function unix2gps(unixTime) {
    'use strict';

    var fpart, gpsTime, ipart;

    ipart = Math.floor(unixTime);
    fpart = unixTime % 1;
    gpsTime = ipart - 315964800;

    if (isunixtimeleap(Math.ceil(unixTime))) {
        fpart *= 2;
    }

    return gpsTime + fpart + countleaps(gpsTime, true);
}

// Convert GPS Time to Unix Time
function gps2unix(gpsTime) {
    'use strict';

    var fpart, ipart, unixTime;
    fpart = gpsTime % 1;
    ipart = Math.floor(gpsTime);
    unixTime = ipart + 315964800 - countleaps(ipart, false);

    if (isleap(ipart + 1)) {
        unixTime = unixTime + fpart / 2;
    } else if (isleap(ipart)) {
        unixTime = unixTime + (fpart + 1) / 2;
    } else {
        unixTime = unixTime + fpart;
    }
    return unixTime;
}

