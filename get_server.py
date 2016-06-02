# coding=utf-8
# __author__ = 'Mio'
from __future__ import division
import sys
import argparse
from multiprocessing import cpu_count, dummy

import requests
import pyping
from lxml import etree
from tqdm import tqdm

reload(sys)
sys.setdefaultencoding('utf-8')


def login(user, password):
    user_info = {'email': user,
                 'password': md5(password),
                 'redirect': '/my'}
    login_uri = 'http://www.ss-link.com/login'

    login_rst = requests.post(login_uri, files=user_info)
    if login_rst.status_code != 200:
        raise Exception(login_rst.text)
    else:
        return login_rst


def md5(password):
    import hashlib
    m = hashlib.md5()
    m.update(password)
    return m.hexdigest()


def get_hosts(login_rst):
    url = "http://www.ss-link.com/my/hostings"
    html = requests.get(url, cookies=login_rst.cookies).content
    return html


def parse_html(html):
    selector = etree.HTML(html)
    a = selector.xpath('//*[@id="main"]/script[6]/text()')[0]

    # a = """
    # jQuery( document ).ready(function() {
    #         jQuery('#main').data('myarray', []);
    #         jQuery('#main').data('n', []);
    #             jQuery('#main').data('myarray').push("45.35.71.119");
    #             n="美国洛杉矶PS线路, 节点45.35.71.119 , 当前负载423";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("45.35.75.57");
    #             n="美国洛杉矶PS线路, 节点45.35.75.57 , 当前负载423";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("45.35.45.35");
    #             n="美国达拉斯PD线路, 节点45.35.45.35 , 当前负载429";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("204.74.217.107");
    #             n="美国硅谷T2线路, 节点204.74.217.107 , 当前负载454";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("204.74.212.195");
    #             n="美国硅谷T2线路, 节点204.74.212.195 , 当前负载455";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("204.74.215.39");
    #             n="美国硅谷T2线路, 节点204.74.215.39 , 当前负载455";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("204.74.216.105");
    #             n="美国硅谷T2线路, 节点204.74.216.105 , 当前负载455";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("72.46.135.119");
    #             n="美国拉斯维加斯VW线路, 节点72.46.135.119 , 当前负载473";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("173.252.220.201");
    #             n="美国硅谷T2线路, 节点173.252.220.201 , 当前负载553";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("104.250.144.10");
    #             n="美国洛杉矶GR线路, 节点104.250.144.10 , 当前负载553";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("76.164.224.102");
    #             n="美国拉斯维加斯VW线路, 节点76.164.224.102 , 当前负载363";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("104.250.143.243");
    #             n="美国洛杉矶GR线路, 节点104.250.143.243 , 当前负载365";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("104.250.146.212");
    #             n="美国洛杉矶GR线路, 节点104.250.146.212 , 当前负载365";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("104.250.146.37");
    #             n="美国洛杉矶GR线路, 节点104.250.146.37 , 当前负载366";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("104.250.147.22");
    #             n="美国洛杉矶GR线路, 节点104.250.147.22 , 当前负载367";
    #             jQuery('#main').data('n').push(n);
    #             jQuery('#main').data('myarray').push("46.249.56.39");
    #             n="欧洲荷兰线路, 节点46.249.56.39 , 当前负载397";
    #             jQuery('#main').data('n').push(n);
    # });
    # """
    b = a.split("push(")

    host_dict = {}
    for i in b:
        index_n = i.find('n="')
        index_end = i.find('";')
        if index_n > -1 and index_end > -1:
            host_info = i[index_n + 3:index_end]
            host_info_list = host_info.split(',')
            host_addr = host_info_list[1].split("节点")[1].strip()
            host_load = int(host_info_list[2].strip().split("当前负载")[1])
            host_name = host_info_list[0]
            host_dict[host_addr] = {"load": host_load, "name": host_name}

    for k, v in host_dict.iteritems():
        print "{:<17}".format(k), "--load: ", "{:<5}".format(v['load']), "--name:  ", v['name']
    print "\n"
    print ">>>>>>>>>> start ping <<<<<<<<<<<<<"
    print "\n"
    return host_dict


def ping_one(ip, ping_count=None):
    if not ping_count:
        ping_count = 3
    r = pyping.ping(ip, count=ping_count, udp=True)
    return {"ip": ip, "avg_rtt": r.avg_rtt}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user", help="account(email)", )
    parser.add_argument("-p", "--password", help="password")
    parser.add_argument("-c", "--ping count", help="ping count", type=int)
    args = parser.parse_args()
    if not (args.user and args.password):
        print("enter your information please")
        user = raw_input("ss-link user: ")
        password = raw_input("ss-link password: ")
    else:
        user, password = args.user, args.password

    if not (user and password):
        raise Exception("没有密码搞毛啊!")
    _login_rst = login(user, password)
    _html = get_hosts(_login_rst)
    # _html = get_hosts(None)
    _host = parse_html(_html)

    # pool = Pool(cpu_count())
    pool = dummy.Pool(cpu_count())
    print "--> start {} threads\n".format(cpu_count())
    multiple_results = [pool.apply_async(ping_one, (_ip, args.ping_count)) for _ip in _host]

    _host_rst = _host.copy()
    with tqdm(total=len(_host), ncols=100, smoothing=0.1, dynamic_ncols=True) as pbar:
        for res in multiple_results:
            ping_rst = res.get()
            _host_rst[ping_rst['ip']]['avg_rtt'] = float(ping_rst['avg_rtt']) if ping_rst['avg_rtt'] else "None"
            pbar.update(1)

    sorted_host = sorted(_host_rst.items(), key=lambda t: t[1]['avg_rtt'], reverse=True)
    print "\n"
    for h in sorted_host:
        print "ip: {:<17} | load: {:<20} | avg_rtt: {:<20} | name: {} ".format(h[0], h[1]['load'],
                                                                               str(h[1]['avg_rtt']), h[1]['name'])

    h_fastest = "ip: {:<17} | load: {:<20} | avg_rtt: {:<20} | name: {} ".format(sorted_host[-1][0],
                                                                                 sorted_host[-1][1]['load'],
                                                                                 sorted_host[-1][1]['avg_rtt'],
                                                                                 sorted_host[-1][1]['name'])

    print "\n"
    print "fastest host:\n"
    print h_fastest
    print "\n bye!"

if __name__ == '__main__':
    main()
