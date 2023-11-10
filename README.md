# scale_pilot
to install this pilot on your raspberry, just do

``` 
sudo su
curl -O https://raw.githubusercontent.com/Auneor/scale_pilot/main/setup.py 
python3 setup.py
``` 

To run manually the scale, 
``` 
python3 balance.py 192.2.22.34 # the ip should be the ip of the scale
``` 

To run manually the scale in test mode with no scale connected: 
``` 
python3 balance.py dummy dummy
``` 
