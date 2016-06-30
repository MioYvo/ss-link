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
    hdr = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, sdch, br",
        "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
        "Connection": "keep-alive",
        "Host": "www.ss-link.com",
        "Referer": "https://www.ss-link.com/login",
        "Upgrade-Insecure-Requests": "1",
    }

    login_rst = requests.post(login_uri, files=user_info, headers=hdr)
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


def ping_one(ip, ping_count=None, su=False):
    if not ping_count:
        ping_count = 3
    r = pyping.ping(ip, count=ping_count, udp=not su)
    _, geo_ip, isp, server = loc_from_ip_cn(ip)
    return {"ip": ip, "avg_rtt": float(r.avg_rtt) if r.avg_rtt else None, "geo_ip": geo_ip, "isp": isp,
            "server": server}


def get_all_hosts():
    url = "https://www.ss-link.com/all"
    res = requests.get(url)
    assert res.ok
    # for ip in res.content.splitlines():
    #     ip = ip.strip()
    #     loc = loc_from_ip_cn(ip)
    return [ip.strip() for ip in res.content.splitlines()]


def loc_from_ip_cn(ip):
    """
    通过ip.cn解析ip位置
    :param ip:
    :return:
    """
    url = "http://ip.cn/index.php"
    loc_res = requests.get(url, params={"ip": ip})
    tree = etree.HTML(loc_res.content)
    isp = tree.xpath('//*[@id="result"]/div/p[2]/code')[0]
    geo_ip = tree.xpath('//*[@id="result"]/div/p[3]')[0]
    server = tree.xpath('//*[@id="result"]/div/p[4]')[0]
    return ip, geo_ip.text, isp, server.text


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument("-u", "--user", help="account(email)", )
    # parser.add_argument("-p", "--password", help="password")
    parser.add_argument("-c", "--ping_count", help="ping count", type=int, default=10)
    parser.add_argument("-s", '--su', help='is su do ?', type=bool, default=False)
    args = parser.parse_args()
    # if not (args.user and args.password):
    #     print("enter your information please")
    #     user = raw_input("ss-link user: ")
    #     password = raw_input("ss-link password: ")
    # else:
    #     user, password = args.user, args.password
    #
    # if not (user and password):
    #     raise Exception("没有密码搞毛啊!")
    # _login_rst = login(user, password)
    # _html = get_hosts(_login_rst)
    # _host = parse_html(_html)

    # pool = Pool(cpu_count())
    _host = get_all_hosts()
    for i in _host:
        print i

    print '\n--> got {} hosts to parse\n'.format(len(_host))

    pool = dummy.Pool(cpu_count())
    print "-->>> su: {}".format(args.su)
    print "--> start {} threads\n".format(cpu_count())
    multiple_results = [pool.apply_async(ping_one, (_ip, args.ping_count, args.su)) for _ip in _host]

    _host_rst = {}
    with tqdm(total=len(_host), ncols=100, smoothing=0.1, dynamic_ncols=True) as pbar:
        for res in multiple_results:
            ping_rst = res.get()
            _host_rst[ping_rst['ip']] = ping_rst
            pbar.update(1)

    sorted_host = sorted(_host_rst.iteritems(), key=lambda t: t[1]['avg_rtt'], reverse=True)
    print "\n"
    for h in sorted_host:
        print "ip: {:<17} | avg_rtt: {:<17} | {:<50} | {:<25} | {}".format(h[0], str(h[1]['avg_rtt']), h[1]['geo_ip'],
                                                                           h[1]['server'], h[1]['isp'])

    h_fastest = "ip: {:<17} | avg_rtt: {:<17} | {:<50} | {:<25} | {}".format(sorted_host[-1][0],
                                                                             sorted_host[-1][1]['avg_rtt'],
                                                                             sorted_host[-1][1]['geo_ip'],
                                                                             sorted_host[-1][1]['server'],
                                                                             sorted_host[-1][1]['isp'])

    print "\n"
    print "fastest host:\n"
    print h_fastest
    print "\nbye!"


if __name__ == '__main__':
    main()
    # ping_one('45.35.71.119')
