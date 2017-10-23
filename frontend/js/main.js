const https = require('https');
const http = require('http');
const url = require('url');

const default_host = {
    hostname: 'api.fmtools.org',
    port: 443
};


// getIndex( result_function, base_uri )
//
// result_function is a function that is called with the JSON body of
// the response from the server to the index request. An `rcomp` index
// request causes all commands that are known by the server to be
// listed.
//
// base_uri (optional) provides the scheme, hostname, and port number
// to which the request should be sent. The default value is
// equivalent to https://api.fmtools.org
exports.getIndex = (function (result_function, base_uri) {
    if (base_uri) {
        var new_host = url.parse(base_uri);
        var options = {
            hostname: new_host.hostname,
            port: new_host.port
        };
        if (new_host.protocol === 'http:') {
            if (options.port == null) {
                options.port = '80';
            }
            var scheme = http;
        } else {  // new_host.protocol === 'https:'
            if (options.port == null) {
                options.port = '443';
            }
            var scheme = https;
        }
    } else {
        var options = default_host;
        var scheme = https;
    }
    var req = scheme.request(options, (res) => {
        res.on('data', (data) => {
            result_function(JSON.parse(data));
        });
    });
    req.end();
    req.on('error', (err) => {
        console.error(err);
    });
});
