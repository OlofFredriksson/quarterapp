# Quarterapp

A personal time tracker for keeping track of what activities you spend your time on during the day. It is not like
a traditional time reporting system, which is primarily designed for extracting data. Quarterapp is designed for
putting in data first, and creating reports second.

The idea is to illustrate each day as 24 rows with 4 columns in each row - 24 hours with 4 quarters. Each quarter
can be tied to a specific activity by color. A day can then summarize how much time you spent in total and per
activity. Quarterapp also supports extracting reports spanning more than a day.


## Usage

Start the server from source using the command: 

    python quarterapp.py

_For installation see GitHub wiki_


## Test

Run the unit test using nose:

    nosetests


## Plugins

Quarterapp has support for three types of plugins, plugins are separate packages / eggs
that are installed (e.g. using pip) using standard methods. Each plugin needs to be
added as an entry point in the setup.py, e.g.

    entry_points = {
        'quarterapp.handlers' : [
            'example = example.plugin:ExamplePlugin',
        ]
    }


### Handler plugin

A plugin may offer one or more additional handlers by implementing a class deriving
from quarterapp.plugin.HandlerPlugin and registering an entry point under the name
'quarterapp.handlers'. 


### View plugin

A plugin may offer one of more additional views. A view is just a handler that also
is displayed in the meny structure. Implement a class that derives from
quarterapp.plugin.ViewPlugin and register an entry point under the name 'quarterapp.views'.


### Storage plugin

Additional storage can be implemented as a plugin. Only one storage will be active at a time,
so the plugin need to fulfil the entire Storage contract.

Implement a class that derives from quarterapp.storage.Storage and register the entry point
under the name 'quarterapp.storages'.


# Contributors

@OlofFredriksson - for fixing issues, early testing and reasoning about features and code.


# License

Copyright © 2013 Markus Eliasson

Distributed under the GPLv3 license