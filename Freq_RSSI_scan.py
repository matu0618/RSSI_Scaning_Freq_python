import bluepy
import numpy as np
import ipget
import matplotlib.pyplot as plt
import pprint
import time
import os
import datetime
import csv
import sys
from concurrent.futures import ThreadPoolExecutor

from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

#=====================================================================
def input_param():
    global data_count, scan_time, cycle_time
    while True:
        try:
            data_count = int(input("測定回数を入力： "))
            scan_time = float(input("RSSI測定のscan time[s]を入力： "))
            cycle_time = float(input("何秒毎の測定かのcycle time[s]を入力： "))
            startOrNot = input("測定を開始しますか？　y/n \n")

            #data_count = 15
            #scan_time = 1.7
            #cycle_time = 2
            #startOrNot = "y"

            startOrNot = "y"
            if startOrNot == "y":
                break
            elif startOrNot == "n":
                print("もう一度入力してください　\n")
                print("Ctrl + c:プログラム終了　\n")
                pass
            else:
                print("もう一度入力してください　\n")
                pass

        except Exception as e:
            print(e, "\n")
            print("もう一度入力してください　\n")
            pass
        except KeyboardInterrupt:
            sys.exit()
#=====================================================================
def set_transmitter_btAddr():
    list = ["time", "b8:27:eb:91:c2:ae", "b8:27:eb:f3:83:9c", "b8:27:eb:6b:2a:4e"]

    return(list)
#=====================================================================
def Scan_RSSI(addr_list, scan_time):
    global scanner

    data_dict = {addr_list[0]:np.nan,
                 addr_list[1]:np.nan, addr_list[2]:np.nan, addr_list[3]:np.nan}
    key_list = list(data_dict.keys())
    #print(key_list)

    scanner = bluepy.btle.Scanner(0)
    devices = scanner.scan(scan_time)

    now_dateTime = datetime.datetime.now()

    data_dict[addr_list[0]] = (str(now_dateTime)[11:19])
        for device in devices:
        if str(device.addr) in key_list:
            if str(device.addr) == addr_list[1]:
                data_dict[addr_list[1]] = ((device.rssi))

            elif str(device.addr) == addr_list[2]:
                data_dict[addr_list[2]] = ((device.rssi))

            elif str(device.addr) == addr_list[3]:
                data_dict[addr_list[3]] = ((device.rssi))

    return data_dict
#=====================================================================
def update_RSSI_data(addr_list, data_dict, update_data_dict):

    update_key_list = list(update_data_dict.keys())
    #print(update_key_list)
    for key_name in data_dict:
        if key_name in update_key_list:
            if key_name == addr_list[0]:
                update_data_dict[addr_list[0]].append(data_dict[addr_list[0]])

            elif key_name == addr_list[1]:
                update_data_dict[addr_list[1]].append(data_dict[addr_list[1]])

            elif key_name == addr_list[2]:
                update_data_dict[addr_list[2]].append(data_dict[addr_list[2]])

            elif key_name == addr_list[3]:
                update_data_dict[addr_list[3]].append(data_dict[addr_list[3]])

    return update_data_dict
#=====================================================================
def Judge_Scan(set_count, scan_time, cycle_time, error_count, addr_list):
    update_data_dict = {addr_list[0]:[],
                        addr_list[1]:[],
                        addr_list[2]:[],
                        addr_list[3]:[]}

    executor_scan = ThreadPoolExecutor(max_workers=2)

    base_time = time.perf_counter()

    elapsed_time = 0
    while True:
        try:
            dt_now = datetime.datetime.now()
            if elapsed_time % cycle_time == 0:
                print("経過時間：{}s".format(elapsed_time))
                data_dict = executor_scan.submit(Scan_RSSI, addr_list, scan_time)
                update_data_dict = update_RSSI_data(addr_list, data_dict.result(), update_data_dict)
                pprint.pprint(update_data_dict)

                array_1 = np.array(update_data_dict[addr_list[1]])
                array_2 = np.array(update_data_dict[addr_list[2]])
                array_3 = np.array(update_data_dict[addr_list[3]])

                print()
                print("{0} {1}".format(len(array_1[~np.isnan(array_1)]), addr_list[1]))
                print("{0} {1}".format(len(array_2[~np.isnan(array_2)]), addr_list[2]))
                print("{0} {1}".format(len(array_3[~np.isnan(array_3)]), addr_list[3]))
                print()

                count_1 = len(array_1[~np.isnan(array_1)])
                count_2 = len(array_2[~np.isnan(array_2)])
                count_3 = len(array_3[~np.isnan(array_3)])

            timer = executor_scan.submit(timer_count, base_time)
            elapsed_time = timer.result()
            # print("経過時間：{}s".format(elapsed_time))
            if count_1 >= set_count and count_2 >= set_count and count_3 >= set_count:
                break

        except Exception as e:
            #traceback.print_exc()
            print(e)
            print("Error (count=" + str(error_count) + ")")
            error_count += 1
            if error_count == 10:
                break
            os.system("sudo systemctl daemon-reload")
            print("Retry")
            pass
             except KeyboardInterrupt:
            sys.exit()


    print("測定終了 \n")
    return(update_data_dict)
#=====================================================================
def timer_count(base_t):
    now_t = time.perf_counter()
    temp_t = "{:.2f}".format(now_t - base_t)
    delta_t = float(temp_t)
    #print(delta_t)
    return(delta_t)
#=====================================================================
def IPget():    #IPアドレスの取得
    a = ipget.ipget()
    ipaddr = str(a.ipaddr("eth0"))
    #ipaddr = str(a.ipaddr("wlan0"))
    return(ipaddr)
#=====================================================================
def list_save_file(name, data_list):
    try:
        print("save as csv ...")
        with open(name, "w") as f:  #リストをcsvファイルにする
            writer = csv.writer(f, lineterminator="\n")
            writer.writerows(data_list)
        print("success! \n")
    except Exception as e:
        #traceback.print_exc()
        print(e)
        pass
#=====================================================================
def dict_save_file(file, save_dict):
    save_row = {}
    try:
        with open(file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=save_dict.keys(), delimiter=",", quotechar='"')
            writer.writeheader()

            k1 = list(save_dict.keys())[0]
            length = len(save_dict[k1])

            for i in range(length):
                for k, vs in save_dict.items():
                    save_row[k] = vs[i]

                writer.writerow(save_row)
    except Exception as e:
        #traceback.print_exc()
        print(e)
        pass
#=====================================================================
def G_upload_scanData(local_file, gdrive_dir , name):
    print("Start Upload")
    for i in range(2):
        try:
            gauth = GoogleAuth()
            gauth.LocalWebserverAuth()
            drive = GoogleDrive(gauth)
            folder_id = drive.ListFile({'q': 'title = "{}"'.format(gdrive_dir)}).GetList()[0]['id']
            f = drive.CreateFile({"parents": [{"id": folder_id}]})
            f.SetContentFile(local_file)
            f['title'] = name
            f.Upload()
            print("success! \n")
        except Exception as e:
            #traceback.print_exc()
            print(e)
            print("Error (count=" + str(i+1) + ")")
            time.sleep(3.0)
            print("Retry")
            pass
        else:
            break
    else:
        print("failure...")
        pass
#=====================================================================
if __name__ == '__main__':
    Error_count = 0

    input_param()

    print("観測データ数：{}".format(data_count))
    print("scan時間[s]：{}".format(scan_time))
    print("測定間隔[s]：{}".format(cycle_time))
    print()

    dt_start = datetime.datetime.now()
    print(dt_start)
    print("start \n")

    addr_list = set_transmitter_btAddr()

    print(addr_list, "\n")

    try:
        data_list = [addr_list, ]    #スレッドで実行した結果を格納
        #print(update_data_dict)
        save_data = Judge_Scan(data_count, scan_time, cycle_time, Error_count, addr_list)
        print()
        pprint.pprint(save_data)
        print()

        ipaddr = IPget()
        #print(ipaddr,"\n")
        dt_now = datetime.datetime.now()
        name =  str(dt_now.year) + "_" + str(dt_now.month) + str(dt_now.day) + "_" + str(dt_now.hour)+ str(dt_now.minute) + "_" + ipaddr[:-2] + ".csv"
        path = "CsvData/" + name
        dict_save_file(path, save_data)

        G_upload_scanData(path, "bluetooth_data", name) #scanしたデータをアップロード

        dt_end = datetime.datetime.now()
        delta_time = dt_end - dt_start
        print()
        print(delta_time)
        print(dt_end)
        print("Finish ! !")

    except KeyboardInterrupt:
        sys.exit()
