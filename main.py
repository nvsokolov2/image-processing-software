#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

import argparse
import socket
import json

VERSION = '0.1.0'
TYPE = 'handler'

if __name__ == '__main__':
    # создаем аргументы для запуска программы
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', default='127.0.0.1')
    parser.add_argument('-port', default=3456)
    args = parser.parse_args()

    # пытаемся подключиться
    try:
        con = socket.create_connection((args.ip, args.port))
        con_file = con.makefile('rw')
    except Exception as err:
        print (err)
        con.close()
        exit()

    # первичное подключение
    con_file.write(json.dumps({
        'action':'init',
        'type':TYPE,
        'version':VERSION
        }) + "\n")
    con_file.flush()

    # ожидание подтверждения от сервера
    try:
        resp = con_file.readline()
        resp = json.loads(resp)

        if resp['action'] != 'approved':
            print ('Server did not approved connection')
            con.close()
            exit()
    except Exception as err:
        print ('Server sended wrong response')
        print ('\t{}'.format(err))
        con.close()
        exit()

    # временный режим echo (отправляет обратно то, что приняли)
    for line in con_file:
        con_file.write(line)
        con_file.flush()

    con.close()
