const https = require('https');
const http = require('http');
const url = require('url');


function createProtoRequest( options, base_uri ) {
    var options = options;
    if (options === undefined) {
        options = {};
    } else if ((typeof options === 'string') && base_uri === undefined) {
        var base_uri = options;
        options = {};
    }
    if (base_uri) {
        var new_host = url.parse(base_uri);
        options.hostname = new_host.hostname;
        options.port = new_host.port;
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
        options.hostname = 'api.fmtools.org';
        options.port = 443;
        var scheme = https;
    }

    return (function (f) {
        return scheme.request(options, f);
    });
}


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
    var reqf = createProtoRequest( base_uri );
    var data = '';
    var req = reqf((res) => {
        res.on('data', (chunk) => {
            data += chunk;
        });
        res.on('end', () => {
            result_function(JSON.parse(data));
        });
    });
    req.on('error', (err) => {
        console.error(err);
    });
    req.end();
});

// getServerVersion( result_function, base_uri )
//
// result_function is a function that is called with the JSON body of
// the response from the server to the index request.
//
// base_uri (optional) provides the scheme, hostname, and port number
// to which the request should be sent. The default value is
// equivalent to https://api.fmtools.org
exports.getServerVersion = (function (result_function, base_uri) {
    var reqf = createProtoRequest( {path: '/version'}, base_uri );
    var data = '';
    var req = reqf((res) => {
        res.on('data', (chunk) => {
            data += chunk;
        });
        res.on('end', () => {
            result_function(JSON.parse(data));
        });
    });
    req.on('error', (err) => {
        console.error(err);
    });
    req.end();
});
