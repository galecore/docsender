# docsender
A small util for sending files to a list of people via python3


Example of valid config file is present below
## Sender 
from = ...

## In order to send file to test recepient use mode TEST instead of NO_SENT
test_recepient = ...

## Subject of the letter
subject_raw = Month {}, year {}
body_raw = Month {}, year {}.

##SMTP server credentials
host = 	...
port = ...
login = ...
password = ...

## CSV file parameters
delimiter = ;