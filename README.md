b3-plugin-ipban
===============

This plugin checks the  IP addresses of clients with an active ban or tempban. So in addition to the GUID check, it also
checks the IP address belonging to the client with the active (temp)ban and kicks if appropriate.

## Installation

1. copy the `extplugins/ipban` folder into your installations `b3/extplugins` folder.
2. load the plugin to your `b3.xml` config file:

        <plugin name="ipban" config="@b3/extplugins/ipban/conf/plugin_ipban.ini"/>

3. modify the config file to your preference
4. restart the bot