## About
clicfg.py is an Asterisk call file generator. It uses a jinja2 template to generate the call files.
In a future version, these two files will likely be combined for ease-of-use and portability.

## Usage
```sh
clicfg.py --channel SIP/1234 --context from-internal --exten 1235
```

The example above would generate a call file that would call SIP/1234, which when answered would
call 1235@from-internal. Those are the only three required arguments.

In future releases, I hope to be able to include the generation of call files that send to an application.
These are not supported currently as I did not have the time to setup nested argument parsers.

## Todo
- Add better logging support
- Application dial support
- Call file handling and spooling

## Author
Rob Ladendorf 2020-09-19
