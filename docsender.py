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
from datetime import datetime


'''stupid python can not stand infinitives'''
months = \
{
    1:"январь",
    2:"февраль",
    3:"март",
    4:"апрель",
    5:"май",
    6:"июнь",
    7:"июль",
    8:"август",
    9:"сентябрь",
    10:"октябрь",
    11:"ноябрь",
    12:"декабрь",
}

def send_mail(smtp_server, send_from, send_to, subject="", text="", files=None):
    '''Sends email with attachments using logged smtp_server object'''
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = ", ".join(send_to)
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

def generate_subject_and_body(raw_code, file_code, subject_raw, body_raw):
    '''Generates subject and body of the letter based on raw code and dummy strings'''
    year, month, _, _ = raw_code.split("_") # year_month_code_
    month = months[int(month)]
    subject = subject_raw.format(file_code, month, year)
    body = body_raw.format(month, year)
    return subject, body

def process_csv(smtp_server, csvfile, config):
    '''Processes strings from csvfile and returns filename of a modified copy of csvfile'''
    with open("tmp_" + basename(csvfile.name), 'w') as tmp:
        reader = csv.reader(csvfile, delimiter=config["delimiter"])
        writer = csv.writer(tmp, delimiter=config["delimiter"], lineterminator="\n")
        for i, row in enumerate(reader):
            if (not row):
                continue
            raw_code, mode, timepoint, price, raw_recepients, company_name, file1, file2, file_code = row
            recepients = list(map(lambda string: string.strip(), raw_recepients.replace("*", "").split(",")))
            send_from = config["from"]    
            subject, body = generate_subject_and_body(raw_code, file_code, config["subject_raw"], config["body_raw"])
            files = [file1.strip(), file2.strip()]

            should_send = True
            if mode.strip() == 'NO_SENT':
                timepoint = datetime.today().strftime("%d.%m.%Y %H:%M")
                print("Sent email on line {}".format(i))
            elif mode.strip() == "TEST":
                recepients = [config["test_recepient"]]
                timepoint = datetime.today().strftime("%d.%m.%Y %H:%M")
                print("Sent email on line {}".format(i))                
            else:
                should_send = False
                print("Ignoring line {}, mode = {}".format(i, mode))

            
            try:
                if should_send:
                    send_mail(smtp_server,
                        send_from=send_from, send_to=recepients, 
                        subject=subject, text=body, files=files)
            except:
                result = "ERROR"
            else:
                result = "SENT"
            finally:
                writer.writerow([raw_code, result, timepoint, price, raw_recepients, company_name, file1, file2, file_code])

    return "tmp_" + basename(csvfile.name)

def open_smtp_server(config):
    '''Opens stmp server connection and logs in using credentials'''
    smtp_server = smtplib.SMTP_SSL(config["host"], config["port"])
    smtp_server.login(config["login"], config["password"])
    return smtp_server

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=argparse.FileType('r'), 
        help="Config file path.")
    parser.add_argument("csv", type=argparse.FileType('r'), 
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