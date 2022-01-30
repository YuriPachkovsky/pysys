import psutil
import json
import time
import sys

GLOBAL_STATE = {}

def load_stat():
    name = "load"
    stat = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
    return {"norm1": stat[0], "norm5": stat[1], "norm15": stat[2], "metrica": name}


def socket_stat():
    name = "socket_summary"
    socket_udp = psutil.net_connections(kind='udp')
    socket_tcp = psutil.net_connections(kind='tcp4')
    return {"tcpAllCount": len(socket_tcp), "udpAllCount": len(socket_udp), "metrica": name}

def network_stat():
    name = "network"
    stat = psutil.net_io_counters(pernic=True)
    result = []
    for i in stat.items():
        info = i[1]
        result.append({   "networkInterface": i[0],
                          "incomingPackages": info.packets_recv,
                          "incomingBytes": info.bytes_recv,
                          "incomingErrors": info.errin,
                          "incomingDropped": info.dropin,
                          "outgoingPackages": info.packets_sent,
                          "outgoingBytes": info.bytes_sent,
                          "outgoingDropped": info.dropout,
                          "outgoingErrors": info.errout,
                          "metrica": name
                        })
    return result

def cpu_stat_init():
    psutil.cpu_times_percent(interval=0)

def cpu_stat():
    name = "cpu"
    cores = psutil.cpu_count()
    stat = psutil.cpu_times_percent(interval=0)
    return {"idle": stat.idle, "ioWait": stat.iowait, "systemCpu": stat.system, "irq": stat.irq, "user": stat.user, "total": stat.system + stat.irq + stat.user, "cores": cores, "metrica": name}


def diskio_stat_init():
    stat = psutil.disk_io_counters(perdisk=True)
    global GLOBAL_STATE
    GLOBAL_STATE['diskio'] = stat, time.time()


def diskio_stat():
    name = "diskio"
    result = []
    stat = psutil.disk_io_counters(perdisk=True)
    global GLOBAL_STATE
    prev_state, prev_time = GLOBAL_STATE["diskio"]
    diff_time = (time.time()-prev_time)
    for i in stat.items():
        prev_item = prev_state.get(i[0])
        info = i[1]
        result.append({ "name": i[0],
                        "readRequestPerSec": (info.read_count - prev_item.read_count) / diff_time,
                        "writeRequestPerSec": (info.write_count - info.write_count) / diff_time,
                        "readPerSecBytes": (info.read_bytes - info.read_bytes)/ diff_time,
                        "writePerSecBytes": (info.write_bytes - info.write_bytes)/ diff_time,
                        "busy": info.busy_time,
                        "metrica": name
                      })
    GLOBAL_STATE['diskio'] = stat, time.time()
    return result


def memory_stat():
    name = "memory"
    stat = psutil.virtual_memory()
    result = { 
            "total": stat.total,
            "usedBytes": stat.used,
            "free": stat.free,
            "actualUsedBytes": stat.total - stat.available,
            "actualUsedPct": stat.percent,
            "metrica": name
            }
    return result

def filesystem_stat():
    name = "fsstat"
    stat = psutil.disk_usage('/')
    return {"free": stat.free, "used": stat.used, "total": stat.total, "metrica": name}

def uptime_stat():
    name = "boot"
    stat = time.time() - psutil.boot_time()
    return {"duration": stat, "metrica": name}

def init_collectors():
    diskio_stat_init()
    cpu_stat_init()

def run():
    first_cycle = True
    flag_add_collectors = True
    collectors = []
    #collectors = [ load_stat, socket_stat, network_stat, cpu_stat, memory_stat, filesystem_stat, uptime_stat ]
    try:
        loop_time = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    except Exception as err:
        print("Need cycle time(integer)")
        sys.exit(-1)
    init_collectors()
    while True:
        if not first_cycle and flag_add_collectors:
            collectors.append(diskio_stat)
            flag_add_collectors = False
        timestamp = time.time()
        for i in collectors:
            stat = i()
            if isinstance(stat, list):
                for elem in stat:
                    elem["timestamp"] = timestamp
                    print(json.dumps(elem))
            else:
                stat["timestamp"] = timestamp
                print(json.dumps(stat))
        if first_cycle:
            first_cycle = False
        time.sleep(loop_time)

if __name__ == "__main__":
    run()
