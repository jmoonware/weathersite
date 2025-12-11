#!/bin/bash
#
MYIP=`curl http://checkip.amazonaws.com`

# Set up a new record first at Dynu
# https://www.dynu.com/en-US/ControlPanel/DDNS
# Then "+add"
# When done editing, drop into /usr/local/bin (and make executable of course)
# Put updatedns.service into /etc/systemd/system
# then 
# systemctl enable updatedns.service

# change this to the correct API key on deployment
DYNUAPIKEY = abcd1234

# this will list DNS record numbers that are needed below
curl -X GET https://api.dynu.com/v2/dns \
	-H "accept:application/json" \
	-H "API-Key: $DYNUAPIKEY" 

# change this to the proper DNS record number and server name
RECNUM = 12345678
SERVERNAME = "server.mydomain.org"

# This POST command updates DNS record of domain
curl -X POST https://api.dynu.com/v2/dns/$RECNUM/ \
	-H "accept:application/json" \
	-H "API-Key: $DYNUAPIKEY" \
	--json '{"name": "'$SERVERNAME'","group": "","ipv4Address": "'$MYIP'","ipv6Address": "","ttl": 90, "ipv4": true,"ipv6": false,"ipv4WildcardAlias": true,"ipv6WildcardAlias": false,"allowZoneTransfer": false,"dnssec": false}'

