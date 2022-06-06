#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

import argparse
import socket
import json

import os
import base64
import binascii
import tempfile

from skimage import io
from skimage import filters
from skimage.color import rgb2gray
from skimage.util import img_as_ubyte

VERSION = '0.2.0'
TYPE = 'handler'

def save_img_as_file(format, data):
    if format == 'image/jpeg':
        suffix = '.jpg'
    elif format == 'image/png':
        suffix = '.png'
    else:
        raise NameError

    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    name = f.name

    f.write(data)
    f.flush()
    f.close()

    return name, suffix

def process_image(file, suffix):
    img = io.imread(file)

    grayscale = rgb2gray(img)
    edge_sobel = filters.sobel(grayscale)

    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    name = f.name
    f.close()

    io.imsave(name, img_as_ubyte(edge_sobel))

    return name

def load_img_from_file(file):
    f = open(file, "r+b")
    data = f.read()
    f.close()
    return data

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
        exit()

    # первичное подключение
    con_file.write(json.dumps({
        'action':'init',
        'type':TYPE,
        'version':VERSION
        }) + '\n')
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

    # обработка полученных изображений
    for line in con_file:
        # TODO: здесь нет error, если мы не смогли распарсить json
        try:
            obj = json.loads(line)
            obj['error'] = False
            obj['error_msg'] = None
        except Exception as err:
            print ('Could not parse incoming message')
            print ('\t{}'.format(err))

            con_file.write(line)
            con_file.flush()
            continue

        try:
            img_data = base64.b64decode(obj['data'])

            file, suffix = save_img_as_file(obj['format'], img_data)
            new_file = process_image(file, suffix)
            new_img = load_img_from_file(new_file)

            os.remove(file)
            os.remove(new_file)

            obj['data'] = base64.b64encode(new_img).decode()
            obj['filename'] = 'sobel_' + obj['filename']
        except KeyError as err:
            obj['error'] = True
            obj['error_msg'] = 'JSON has no key {}'.format(err)
            print (obj['error_msg'])
        except binascii.Error as err:
            obj['error'] = True
            obj['error_msg'] = 'Could not convert data from base64'
            print (obj['error_msg'])
            print ('\t{}'.format(err))
        except NameError as err:
            obj['error'] = True
            obj['error_msg'] = 'Wrong image format'
            print (obj['error_msg'])
        except Exception as err:
            obj['error'] = True
            obj['error_msg'] = 'Image processing error'
            print (obj['error_msg'])
            print ('\t{}'.format(err))

        con_file.write(json.dumps(obj) + '\n')
        con_file.flush()

    con.close()
