#!/bin/env node
// Command-line interface for `rcomp` JS client
//
// In general this module (cli.js) is intended to be used as a NodeJS
// script in a terminal, not within a browser.  Core implementation is
// in other files, in particular main.js, which can be used in other
// programs, whether NodeJS scripts or Web apps. cli.js is not
// necessary if you are embedding this client into JS code that is
// intended for use in a Web browser.

const main = require('./main.js');


// Defaults
var base_uri = undefined;

var ind = 2;
var print_help = false;
while (process.argv[ind]) {
    if (process.argv[ind] == '-h' || process.argv[ind] == '--help') {
        console.log('cli.js [-h] [-s URI] [COMMAND [ARG [ARG...]]]');
        print_help = true;
        break;
    } else if (process.argv[ind] == '-s') {
        if (process.argv.length - 1 <= ind) {
            throw 'Missing parameter URI of switch `-s`';
        }
        base_uri = process.argv[ind+1];
        ind += 1;
    } else {
        break;
    }
    ind += 1;
}
if (!print_help) {
    if (process.argv[ind] == 'version') {
        main.getServerVersion(function (res) {
            console.log(res);
        },
                              base_uri);
    } else if (process.argv[ind] === undefined) {
        main.getIndex(function (res) {
            for (var command in res.commands) {
                console.log(String(command) + '\t\t' + res.commands[command]['summary']);
            }
        },
                      base_uri);
    } else {
        const command = process.argv[ind];
        main.find_files(command, process.argv.slice(ind+1), function (argv) {
            main.callGeneric(command, argv,
                             function (res) {
                                 if (res['output'].length > 0) {
                                     console.log(res['output'].trim());
                                 }
                                 process.exitCode = res['ec'];
                             },
                             base_uri);
        });
    }
}
