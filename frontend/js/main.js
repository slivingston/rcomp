// main module of `rcomp` JS client
//
// For an example of using this in command-line applications, read cli.js

const https = require('https');
const http = require('http');
const url = require('url');


// createProtoRequest( options, base_uri )
//
// construct request for an `rcomp` server. The scheme etc. are
// determined from base_uri, if given. Otherwise, the default
// https://api.fmtools.org is used.
//
// This function is intended for the internal implementation of this
// client library, and the API for it may change without warning.
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

// callGeneric( cmd, argv, result_function, base_uri )
//
// cmd is the remote program name, e.g., `ltl2ba`.
//
// argv is an array of arguments, where file names may be replaced by
// base64-encoded copies of local files.
//
// result_function is a function that is called with the JSON body of
// the response from the server to the index request.
//
// base_uri (optional) provides the scheme, hostname, and port number
// to which the request should be sent. The default value is
// equivalent to https://api.fmtools.org
exports.callGeneric = (function (cmd, argv, result_function, base_uri) {
    var body = JSON.stringify({
        argv: argv
    });
    var options = {
        path: '/'+cmd,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(body)
        }
    };
    var reqf = createProtoRequest( options, base_uri );
    var data = '';
    var req = reqf((res) => {
        res.on('data', (chunk) => {
            data += chunk;
        });
        res.on('end', () => {
            var msg = JSON.parse(data);
            if (msg['done']) {
                result_function(msg);
            } else {
                var timeout = undefined;
                timeout = setInterval((job_id) => {

                    var reqf = createProtoRequest( {path: '/status/'+job_id}, base_uri );
                    var data = '';
                    var req = reqf((res) => {
                        res.on('data', (chunk) => {
                            data += chunk;
                        });
                        res.on('end', () => {
                            var msg = JSON.parse(data);
                            if (msg['done']) {
                                clearInterval(timeout);
                                result_function(msg);
                            }
                        });
                    });
                    req.on('error', (err) => {
                        console.error(err);
                    });
                    req.end();

                                     },
                                      300,
                                      msg['id']);
            }
        });
    });
    req.on('error', (err) => {
        console.error(err);
    });
    req.write(body);
    req.end();
});
