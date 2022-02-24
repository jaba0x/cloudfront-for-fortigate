### Amazon CloudFront address list generator for FortiGate Firewalls

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/2560px-Amazon_Web_Services_Logo.svg.png" alt="Powered by AWS Cloud Computing" width="100"> **+** <img src="https://www.fortinet.com/content/dam/fortinet/images/general/fortinet-logo.svg" alt="Powered by Fortinet" width="200">

Description:
Fetch ip ranges from official AWS source, filter and prepare for FortiGate firewall.
Use with **Python3!**

Prerequisites:
 ```sh
 pip install awsipranges
 ```
 
  ```sh
 pip install requests
 ```
 
 Usage guide:
 ```sh
 python3 generate.py
 ```
 or
  ```sh
 python3 generate.py >> output.txt
 ```

Example:
 ```
 jaba@M1 ~ % python3 generate.py
config firewall address 
 edit CLOUDFRONT1 
 set subnet 120.52.22.96/27 
 end
config firewall addrgrp 
 edit CLOUDFRONT 
 select member CLOUDFRONT1 
 end
config firewall address 
 edit CLOUDFRONT2 
 set subnet 205.251.249.0/24 
 end
config firewall addrgrp 
 edit CLOUDFRONT 
 select member CLOUDFRONT2 
 end
 ...
 
 ```
