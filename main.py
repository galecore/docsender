import csv
import smtplib
import os
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

from contextlib import redirect_stdout, redirect_stderr
import argparse


def send_mail(smtp_server, send_from, send_to, subject="", text="", files=None):
    '''Sends email with attachments using logged smtp_server object'''
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as binary_file:
            part = MIMEApplication(binary_file.read(), Name=basename(f))
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)

    smtp_server.sendmail(send_from, send_to, msg.as_string())

def read_configuration(config_file):
    '''Reads configuration from opened file, config format: key = value'''

    conf = {}
    with config_file as f:
        lines = f.read().splitlines()
        lines = list(filter(lambda x: x.strip() != "" and x.strip()[0] != "#", lines))
        lines = list(map(lambda l: map(lambda x: x.strip(), l.split("=")), lines))
        for line in lines:
            k, v = line
            conf[k] = v
    return conf


def process_csv(smtp_server, csvfile, config):
    '''Processes strings from csvfile and returns filename of a modified copy of csvfile'''
    with open("tmp_" + basename(csvfile.name), 'w') as tmp:
        reader = csv.reader(csvfile, delimiter=config["delimiter"])
        writer = csv.writer(tmp, delimiter=config["delimiter"])
        for i, row in enumerate(reader):
            filename, mode, timepoint, price, raw_recepient, company_name = row
            recepient = raw_recepient.replace("*", "").strip()

            if mode.strip() == 'NO_SENT':
                send_mail(smtp_server, 
                    send_from=config["from"], send_to=recepient, 
                    subject=config["subject"], text=config["body"], files=[filename])
                timepoint = formatdate(localtime=True)
                print("Sent email on line {}".format(i))
            elif mode.strip() == "TEST":
                send_mail(smtp_server, 
                    send_from=config["from"], send_to=config["test_recepient"], 
                    subject=config["subject"], text=config["body"], files=[filename])
                timepoint = formatdate(localtime=True)
                print("Sent email on line {}".format(i))                
            elif mode.strip() == "SENT":
                print("Ignoring line {}, file is sent".format(i))
            else:
                print("Ignoring line {}, unkown mode = {}".format(i, mode))

            writer.writerow([filename, "SENT", timepoint, price, raw_recepient, company_name])

    return "tmp_" + basename(csvfile.name)

def open_smtp_server(config):
    '''Opens stmp server connection and logs in using credentials'''
    smtp_server = smtplib.SMTP_SSL(config["host"], config["port"])
    smtp_server.login(config["login"], config["password"])
    return smtp_server

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=argparse.FileType('r', encoding='UTF-8'), 
        help="Config file path.")
    parser.add_argument("csv", type=argparse.FileType('r', encoding='UTF-8'), 
        help="Input CSV file path")

    args = parser.parse_args()

    with open("logfile.log", "w") as logger, redirect_stdout(logger), redirect_stderr(logger):
        config = read_configuration(args.config)
        smtp_server = open_smtp_server(config)
        tmp_filename = process_csv(smtp_server, args.csv, config)
        csv_filename = args.csv.name
        args.csv.close()
        os.replace(src=tmp_filename, dst=csv_filename)    

main()