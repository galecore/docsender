# docsender
A small util for sending files to a list of people via python3


Example of valid config file is present below
## Sender 
from = ...

## In order to send file to test recepient use mode TEST instead of NO_SENT
test_recepient = ...

## Subject and body of the letter
subject = Testing
body = Testing

## SMTP server credentials
host = 	smtp.yandex.ru
port = 465
login = ...
password = ...

## CSV file parameters
delimiter = ;