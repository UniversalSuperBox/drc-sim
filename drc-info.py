import codecs
import json
import select
import socket
import sys
import time
from threading import Thread

from drcsim.server.data.struct import input, command

PORT_WII_MSG = 50010
PORT_WII_VID = 50020
PORT_WII_AUD = 50021
PORT_WII_HID = 50022
PORT_WII_CMD = 50023

sock_cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_cmd.bind(("192.168.1.10", PORT_WII_CMD))
sock_msg = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_msg.bind(("192.168.1.10", PORT_WII_MSG))
sock_hid = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_hid.bind(("192.168.1.10", PORT_WII_HID))
sock_vid = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_vid.bind(("192.168.1.10", PORT_WII_VID))
sock_aud = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_aud.bind(("192.168.1.10", PORT_WII_AUD))

json_dump = {}


def print_packet(sock, name):
    data = sock.recv(2048)
    print("%s: %s" % (name, codecs.encode(data, "hex").decode()))


def print_packet_cmd(sock):
    data = sock.recv(2048)
    print("cmd: %s" % codecs.encode(data, "hex").decode())
    header = command.header.parse(data)
    if header.packet_type != 2:  # Only accept response packets
        return
    size = 8  # header size
    if header.cmd_id == 1:
        data_string = codecs.encode(data[size:], "hex").decode()
        print("cmd 1: %s" % data_string)
        json_dump["1"] = data_string
    elif header.cmd_id == 0:
        data_string = codecs.encode(data[size + command.header_cmd0.sizeof():], "hex").decode()
        print("cmd 0 %d %d: %s" % (header.id_primary, header.id_secondary, data_string))
        if "0" not in json_dump:
            json_dump["0"] = {}
        if str(header.id_primary) not in json_dump["0"]:
            json_dump["0"][str(header.id_primary)] = {}
        json_dump["0"][str(header.id_primary)][str(header.id_secondary)] = data_string


def send_cmd(data):
    sock_cmd.sendto(data, ("192.168.1.11", PORT_WII_CMD + 100))


def send_command_from_string(command_string, sid):
    send_data = command.header.parse(codecs.decode(command_string, "hex"))
    send_data.seq_id = sid
    if send_data.cmd_id == 1:
        send_data.mic_enabled = 0  # floods logs with audio data if enabled
    send_data = command.header.build(send_data)
    send_cmd(send_data)
    sid += 1
    sid %= 65535
    time.sleep(1)
    return sid


def cmd_request():
    sid = 0
    while True:
        data = {
            0: {0: {0: "000000000c0005087e0115880040000000000000",  # TODO construct these
                    10: "000000000d0005007e0101780040000a0000000100"},
                4: {4: "000000000c0005007e0109780040040400000000",
                    10: "000000000d0005117e012fc80040040a0000000100",
                    11: "000000000c0005017e0107180040040b00000000"},
                5: {6: "000000000c0005007e0101a80040050600000000",
                    12: "00000000110005007e0102f80040050c000000050e0300870f",
                    16: "0000010030000580010000000000000000000000803e0000000100029e0000000000000070000000404003002d0000"
                        "018000400000000000",  # FIXME 0 5 16 is a CMD 1 broadcast - missing actual request
                    24: "00000000160005007e0101c8004005180000000a54313936333030303030"}
                },
            1: "000001003000051a010000000000000000000000803e000000010002000000000000000070000000404003002d00000"
               "10000000000000000"
        }
        for cmd in data.keys():
            if isinstance(data[cmd], str):
                print("Sending command %d" % cmd)
                sid = send_command_from_string(data[cmd], sid)
            else:
                for primary_id in data[cmd].keys():
                    for secondary_id in data[cmd][primary_id].keys():
                        print("Sending command %d %d %d" % (cmd, primary_id, secondary_id))
                        sid = send_command_from_string(data[cmd][primary_id][secondary_id], sid)


def print_hid(sock):
    data = sock.recv(2048)
    input_parsed = input.input_data.parse(data)
    print(input_parsed)


if __name__ == '__main__':
    hid = len(sys.argv) > 1 and sys.argv[1] == "--hid"

    if not hid:
        send_thread = Thread(target=cmd_request)
        send_thread.daemon = True
        send_thread.start()

    while True:
        try:
            rlist, wlist, xlist = select.select((sock_cmd, sock_msg, sock_hid, sock_vid, sock_aud), (), (), 1)
            if rlist:
                for s in rlist:
                    if s == sock_hid and hid:
                        print_hid(s)
                    if hid:
                        continue
                    if s == sock_aud:
                        print_packet(s, "aud")
                    elif s == sock_vid:
                        print_packet(s, "vid")
                    elif s == sock_cmd:
                        print_packet_cmd(s)
                    elif s == sock_msg:
                        print_packet(s, "msg")
        except KeyboardInterrupt:
            if not hid:
                dump = open("region_dump.json", "w")
                dump.write(json.dumps(json_dump, indent=4))
                dump.close()
                print("Wrote dump to region_dump.json")
            sys.exit(0)
