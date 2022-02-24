### Amazon CloudFront address list generator for FortiGate Firewalls
### Author: Jaba Macharashvili
### Date: 24.02.2022
### E-Mail: jaba@jaba.ge
### Webpage: https://jaba.ge

import json
import requests

aws_ip_ranges_url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
aws_ip_ranges = json.loads(requests.get(aws_ip_ranges_url).text)
x = 0

for ip_range in aws_ip_ranges["prefixes"]:
    if ip_range["service"] == "CLOUDFRONT":
        x+=1
        # generate address object
        print("config firewall address", "\n", "edit", ip_range["service"]+str(x), "\n", "set subnet", ip_range["ip_prefix"], "\n", "end")
        # add address object to address group object
        print("config firewall addrgrp", "\n", "edit", ip_range["service"], "\n", "select member", ip_range["service"]+str(x), "\n", "end")
