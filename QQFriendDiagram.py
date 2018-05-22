'''

两个比较重要的变量的结构，虽然不是很好，但是懒得改了(特别是friend_list, 自己都嫌弃)
all_qq=[[qq1, qq2, ...][name1. name2, ...]]
二维列表，all_qq[0]为QQ号(str类型)，all_qq[1][i]为all_qq[0][i]对应的昵称(str类型)

frends_list = [qq, {'uin': friend1_qq, 'friends': [friend_friend_1,friend_friend_2, ...]}, {...}, ...]
list类型，第一个元素为自己的qq(str类型)
第二个元素开始为dict类型
key: uin, friends    uin为好友qq(str类型)，friends为好友的好友列表(列表内的元素为str类型的qq)

'''
import requests
import os
import time
import re
import json
import math
import hashlib
import webbrowser
from http import server as httpServer
from bs4 import BeautifulSoup

def setXY(r, angle):
	x = r*math.cos(angle)
	y = r*math.sin(angle)
	return x,y

#获取登录授权二维码
def getQr(qzone_session):
	get_qr_params = {
		'appid': '549000912',
		'e': '2',
		'l': 'M',
		's': '3',
		'd': '72',
		'v': '4',
		'daid': '5',
		'pt_3rd_aid': '0'
	}
	get_qr_url = 'https://ssl.ptlogin2.qq.com/ptqrshow'
	qzone_respon = qzone_session.get(get_qr_url, params=get_qr_params)
	img = qzone_respon.content
	with open('img.png', 'wb+') as f:
		f.write(img)
		f.close()
	os.startfile('img.png')
	return qzone_session

#登录QQ空间
def qzoneLogin():
	#获取ptqetoken参数
	def getPtQrToken(qrsig):
		hashes = 0
		for letter in qrsig:
			hashes += (hashes<<5)+ord(letter)
		return str(2147483647&hashes)

	qr_login_params = {
		'u1': 'https://qzs.qq.com/qzone/v5/loginsucc.html?para=izone',
		'ptredirect': '0',
		'h': '1',
		't': '1',
		'g': '1',
		'from_ui': '1',
		'ptlang': '2052',
		'js_ver': '10270',
		'js_type': '1',
		'pt_uistyle': '40',
		'aid': '549000912',
		'daid': '5'
	}

	android_ua = 'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36'
	qzone_session = requests.session()
	qzone_session.headers['User-Agent'] = android_ua
	qzone_session = getQr(qzone_session)
	qr_login_params['ptqrtoken'] = getPtQrToken(qzone_session.cookies['qrsig'])

	#间隔1秒轮询二维码状态
	while True:
		qzone_respon = qzone_session.get('https://ssl.ptlogin2.qq.com/ptqrlogin', params=qr_login_params)

		print(qzone_respon.text)	#打印二维码状态

		if qzone_respon.text.find('登录成功') != -1:
			if os.path.exists('img.png'):
				os.remove('img.png')
			break
		if qzone_respon.text.find('二维码已失效') != -1:
			qzone_session = getQr(qzone_session)
		time.sleep(1)

	#获取跳转链接
	qzone_url = re.findall("ptuiCB\('0','0','(.*?)'", qzone_respon.text)[0]
	qzone_respon = qzone_session.get(qzone_url)
	return qzone_session

#爬取好友列表(all_qq)和好友间的好友关系(friend_list)
def getFriends():

	#获取g_tk参数
	def getGTK(p_skey):
	    hashes = 5381
	    for letter in p_skey:
	        hashes += (hashes << 5) + ord(letter) 
	    return str(hashes & 0x7fffffff)

	qzone_session = qzoneLogin()
	friend_list_params = {
		'g_tk': getGTK(qzone_session.cookies['p_skey']),
		'res_uin':'',
		'res_type':'normal',
		'format':'json',
		'count_per_page':'10',
		'page_index':'0',
		'page_type':'0'
	}

	friend_feeds_params = {
		'i_uin':'',
		'i_login_uin':'',
		'mode':'4',
		'previewV8':'1',
		'style':'25',
		'version':'8',
		'showcount':'5',
		'MORE_FEEDS_CGI':'http://ic2.qzone.qq.com/cgi-bin/feeds/feeds_html_act_all',
		'refer':'2'
	}
	all_qq = [[], []]
	my_index_url = 'https://h5.qzone.qq.com/mqzone/profile/'
	my_friend_list_url = 'https://mobile.qzone.qq.com/friend/mfriend_list'
	friend_feeds_url = 'https://h5.qzone.qq.com/proxy/domain/ic2.qzone.qq.com/cgi-bin/feeds/feeds_html_module'

	qzone_respon = qzone_session.get(my_index_url)
	my_qq_uin = str(re.findall('"userid":(.*?),', qzone_respon.text)[0])		#获取自己的QQ号
	all_qq[0].append(my_qq_uin)
	all_qq[1].append('我')
	friend_list_params['res_uin'] = my_qq_uin
	qzone_respon = qzone_session.get(my_friend_list_url, params=friend_list_params)
	friend_list = [my_qq_uin]

	#遍历自己的好友列表
	for friend in json.loads(qzone_respon.text)['data']['list']:
		if str(friend['uin']) in all_qq[0]:	#若此qq号已存在
			continue
		elif len(friend['remark'])>0 :
			#这里为了不必要的信息泄露，对qq号进行了打码处理
			name = '%s\n(%s***%s)' % (friend['remark'], str(friend['uin'])[:3], str(friend['uin'])[6:])
			friend_list.append({'uin': str(friend['uin']), 'friends': []})
		else:
			#同上的打码处理
			name = '%s\n(%s***%s)' % (friend['nick'], str(friend['uin'])[:3], str(friend['uin'])[6:])
			friend_list.append({'uin': str(friend['uin']), 'friends': []})
		all_qq[0].append(str(friend['uin']))
		all_qq[1].append(name)

	#print(friend_list)

	friend_feeds_params['i_login_uin'] = my_qq_uin
	for index in range(1, len(friend_list)):
		if my_qq_uin == str(friend_list[index]['uin']):
			continue
		friend_feeds_params['i_uin'] = friend_list[index]['uin']
		qzone_respon = qzone_session.get(friend_feeds_url, params=friend_feeds_params)
		qzone_respon.encoding = 'utf-8'

		soup = BeautifulSoup(qzone_respon.text, 'lxml')
		likes = soup.select('.user-list > a')
		for like in likes:
			uin = str(like.get('href').split('/')[-1])
			#name = '%s\n(%s***%s)' % (like.text, str(uin[:3]), str(uin[6:]))	#非你好友的点赞人员若也要爬取，需要取消注释此句

			#此条件只爬取你们的共同好友，若要爬取非你的好友的需要删除 and (uin in all_qq[0])  条件
			if (uin not in friend_list[index]['friends']) and (uin in all_qq[0]):
				friend_list[index]['friends'].append(uin)
			print('qq:\t\t\t%s' % uin)
			print('nickName:\t%s' % name)

			#非你好友的点赞人员若也要爬取，需要取消注释以下代码
			# if uin not in all_qq[0]:
			# 	all_qq[0].append(uin)
			# 	all_qq[1].append(name)

		time.sleep(2)	#千！万！不！要！为了提高速度删掉这个！！！！你的QQ会被冻结的！！！！！(我不知道改成1会不会冻结，不敢试了)

	return all_qq, friend_list

#保存数据
def saveData(all_qq, friend_list):
	#一个node表示一个人,用edge来表示好友关系
	my_data = {
		'nodes': [],
		'edges': []
	}
	radius = 8000	#最后的图为一个圆形，此为半径
	salt = '666666'


	for qq_index in range(len(all_qq[0])):
		md5 = hashlib.md5()
		#为了防止信息泄露，将qq号进行md5加盐哈希处理（其实这个也不咋保险，但是应该没人特意搞这个，所以想着js那边做一下混淆就已经不太好还原了）
		md5.update((all_qq[0][qq_index]+salt).encode('utf-8'))
		node_id = md5.hexdigest()
		qq_node = {
			'id': node_id,
			'label': all_qq[1][qq_index],
			'size': 1,
			'color': '#f7f7f7'
		}
		my_data['nodes'].append(qq_node)

	my_data['nodes'][0]['size'] = 6
	my_data['nodes'][0]['color'] = '#7299a7'
	my_data['nodes'][0]['x'], my_data['nodes'][0]['y'] = 8000, 8000		#圆心也就是自己的坐标

	#生成对应的edge
	for index in range(1, len(friend_list)):
		qq = friend_list[index]['uin']
		if qq == friend_list[0]:
			continue
		my_data['nodes'][all_qq[0].index(qq)]['size'] = 3
		my_data['nodes'][all_qq[0].index(qq)]['color'] = '#f3456d'
		pi = math.pi
		angle = index * (2*pi/(len(friend_list)))
		x, y = setXY(8000, angle)
		print(x, y)
		my_data['nodes'][all_qq[0].index(qq)]['x'] = 8000 + x
		my_data['nodes'][all_qq[0].index(qq)]['y'] = 8000 + y
		md5 = hashlib.md5()
		md5.update((friend_list[0]+salt).encode('utf-8'))
		source_md5 = md5.hexdigest()
		md5 = hashlib.md5()
		md5.update((qq+salt).encode('utf-8'))
		qq_md5 = md5.hexdigest()
		my_edge = {
			'id': source_md5 + '_' + qq_md5,
			'source': source_md5,
			'target': qq_md5,
			'size': 6,
			'color': '#ccc'
		}
		my_data['edges'].append(my_edge)

		for friend in friend_list[index]['friends']:
			md5 = hashlib.md5()
			md5.update((friend+salt).encode('utf-8'))
			target_md5 = md5.hexdigest()
			qq_edge = {
				'id': qq_md5 + '_' + target_md5,
				'source': qq_md5,
				'target': target_md5,
				'size': 3,
				'color': '#ccc'
			}
			my_data['edges'].append(qq_edge)

	#将数据保存为json文件
	with open('my_data.json', 'w+') as f:
		f.write(json.dumps(my_data))
		f.close()

all_qq, friend_list = getFriends()
# print(all_qq)
# print('-'*20)
# print(friend_list)

saveData(all_qq, friend_list)

webbrowser.open('http://127.0.0.1:6666')
httpServer.test(HandlerClass=httpServer.SimpleHTTPRequestHandler, port=6666)






