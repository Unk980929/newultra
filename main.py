from cProfile import run
import pstats
from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

from JDatabase import JsonDatabase
import zipfile
import os
import nmap
import infos
import xdlink
import mediafire
from megacli.mega import Mega
import megacli.megafolder as megaf
import megacli.mega
import datetime
import time
import youtube
import multiFile
import NexCloudClient
from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import tlmedia
import json
import asyncio
import aiohttp
import S5Crypto
import cryptocode
from yarl import URL
import re
from draft_to_calendar import send_calendar


def sign_url(token: str, url: URL):
    query: dict = dict(url.query)
    query["token"] = token
    path = "webservice" + url.path
    return url.with_path(path).with_query(query)

def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'📦𝙿𝚛𝚎𝚙𝚊𝚛𝚊𝚗𝚍𝚘 𝚙𝚊𝚛𝚊 𝚜𝚞𝚋𝚒𝚛☁...')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            itererr = 0
            if loged:
                if user_info['uploadtype'] == 'evidence':
                    evidences = client.getEvidences()
                    evidname = str(filename).split('.')[0]
                    for evid in evidences:
                        if evid['name'] == evidname:
                            evidence = evid
                            break
                    if evidence is None:
                        evidence = client.createEvidence(evidname)

                originalfile = ''
                if len(files)>1:
                    originalfile = filename
                draftlist = []
                for f in files:
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    tokenize = False
                    if user_info['tokenize']!=0:
                       tokenize = True
                    while resp is None:
                          if user_info['uploadtype'] == 'evidence':
                             fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                          elif user_info['uploadtype'] == 'draft':
                                fileid,resp = client.upload_file_draft(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                                draftlist.append(resp)
                          elif user_info['uploadtype'] == 'perfil':
                                fileid,resp = client.upload_file_perfil(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                                draftlist.append(resp)
                          elif user_info['uploadtype'] == 'blog':
                                fileid,resp = client.upload_file_blog(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                                draftlist.append(resp)
                          elif user_info['uploadtype'] == 'calendar':
                                fileid,resp = client.upload_file_calendar(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                                draftlist.append(resp)
                          iter += 1
                          if iter>=10:
                              break
                    os.unlink(f)
                if user_info['uploadtype'] == 'evidence':
                    try:
                        client.saveEvidence(evidence)
                    except:pass
                return draftlist
            else:
                bot.editMessageText(message,'⚠️𝙴𝚛𝚛𝚘𝚛 𝚎𝚗 𝚕𝚊 𝚗𝚞𝚋𝚎⚠️')
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            bot.editMessageText(message,'🚀Subiendo ☁ Espere por favor...😄')
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               filesdata = []
               for f in files:
                   data = client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)
               return filesdata
        return None
    except Exception as ex:
        bot.editMessageText(message,f'⚠️𝙴𝚛𝚛𝚘𝚛 {str(ex)}⚠️')


def processFile(update,bot,message,file,thread=None,jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        client = processUploadFiles(file,file_size,[file],update,bot,message,jdb=jdb)
        file_upload_count = 1
    bot.editMessageText(message,'📦𝙿𝚛𝚎𝚙𝚊𝚛𝚊𝚗𝚍𝚘 𝚊𝚛𝚌𝚑𝚒𝚟𝚘📄...')
    evidname = ''
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidname = str(file).split('.')[0]
                    txtname = evidname + '.txt'
                    evidences = client.getEvidences()
                    for ev in evidences:
                        if ev['name'] == evidname:
                           files = ev['files']
                           break
                        if len(ev['files'])>0:
                           findex+=1
                    client.logout()
                except:pass
            if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype'] == 'calendar' or getUser['uploadtype'] == 'perfil':
               for draft in client:
                   files.append({'name':draft['file'],'directurl':draft['url']})
        else:
            for data in client:
                files.append({'name':data['name'],'directurl':data['url']})
        bot.deleteMessage(message.chat.id,message.message_id)
        finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        if len(files)>0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
        try:
            import urllib
            user_info = jdb.get_user(update.message.sender.username)
            cloudtype = user_info['cloudtype']
            proxy = ProxyCloud.parse(user_info['proxy'])
            if cloudtype == 'moodle':
                client = MoodleClient(user_info['moodle_user'],
                                    user_info['moodle_password'],
                                    user_info['moodle_host'],
                                    user_info['moodle_repo_id'],
                                    proxy=proxy)
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            if getUser['uploadtype'] == 'calendar' or getUser['uploadtype'] == 'draft':
                nuevo = []
                #if len(files)>0:
                    #for f in files:
                        #url = urllib.parse.unquote(f['directurl'],encoding='utf-8', errors='replace')
                        #nuevo.append(str(url))
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    nuevo.append(f['directurl']+separator)
                    fi += 1
                urls = asyncio.run(send_calendar(host,user,passw,nuevo))
                loged = client.login()
                if loged:
                    token = client.userdata
                    modif = token['token']
                    client.logout()
                nuevito = []
                for url in urls:
                    url_signed = (str(sign_url(modif, URL(url))))
                    nuevito.append(url_signed)
                loco = '\n'.join(map(str, nuevito))
                fname = str(txtname)
                with open(fname, "w") as f:
                    f.write(str(loco))
                #fname = str(randint(100000000, 9999999999)) + ".txt"
                bot.sendMessage(message.chat.id,'𝙴𝙽𝙻𝙰𝙲𝙴𝚂 𝙳𝙸𝚁𝙴𝙲𝚃𝙾𝚂 𝙳𝙴 𝙲𝙰𝙻𝙴𝙽𝙳𝙰𝚁𝙸𝙾👇')
                bot.sendFile(update.message.chat.id,fname)
            else:
                return
        except:
            bot.sendMessage(message.chat.id,'💢𝙽𝙾 𝚂𝙴 𝙿𝚄𝙳𝙾 𝙼𝙾𝚅𝙴𝚁 𝙰 𝙲𝙰𝙻𝙴𝙽𝙳𝙰𝚁𝙸𝙾💢')
    else:
        bot.editMessageText(message,'⚠️𝙴𝚛𝚛𝚘𝚛 𝚎𝚗 𝚕𝚊 𝚗𝚞𝚋𝚎⚠️')

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)
        else:
            bot.editMessageText(message,'》Enlaces de MEGA no soportados')

# def megadl(update,bot,message,megaurl,file_name='',thread=None,jdb=None):
#     megadl = megacli.mega.Mega({'verbose': True})
#     megadl.login()
#     try:
#         info = megadl.get_public_url_info(megaurl)
#         file_name = info['name']
#         megadl.download_url(megaurl,dest_path=None,dest_filename=file_name,progressfunc=downloadFile,args=(bot,message,thread))
#         if not megadl.stoping:
#             processFile(update,bot,message,file_name,thread=thread)
#     except:
#         files = megaf.get_files_from_folder(megaurl)
#         for f in files:
#             file_name = f['name']
#             megadl._download_file(f['handle'],f['key'],dest_path=None,dest_filename=file_name,is_public=False,progressfunc=downloadFile,args=(bot,message,thread),f_data=f['data'])
#             if not megadl.stoping:
#                 processFile(update,bot,message,file_name,thread=thread)
#         pass
#     pass

def clearDraft():
    try:
        files = os.listdir(os.getcwd())
        for f in files:
            if '.' in f:
                if conf.ExcludeFiles.__contains__(f):
                    print('No se pudo eliminar: '+f)
                else:
                    os.remove(f)
    except Exception as e:
        print(str(e))  

def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                bot.sendFile(update.message.chat.id,name)
                os.unlink(name)

def broadcast(username):
    obj = json.load(open("database.jdb"))   
    data = str(obj)                                               
    for broad in xrange(len(obj)):
        obj[username]['broadcast']
    return broad

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        tl_admin_user = os.environ.get('tl_admin_user')

        #set in debug
        tl_admin_user = os.environ.get('administrador')

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)

        if username == tl_admin_user or user_info :  # validate user
            if user_info is None:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:return
        


        msgText = ''
        try: msgText = update.message.text
        except:pass

        # comandos de admin
        if '/add' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    msg = '✅El usuario @'+user+' ah sido agregado al bot!'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'⚠️Error en el comando /add usuario')
            else:
                bot.sendMessage(update.message.chat.id,'⚠️No posee permisos de administrador⚠️')
            return
        if '/admin' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_admin(user)
                    jdb.save()
                    msg = '🌟Ahora @'+user+' es admin del bot también.'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'⚠️Error en el comando /admin usuario⚠️')
            else:
                bot.sendMessage(update.message.chat.id,'⚠️No posee permisos de administrador⚠️')
            return

        if '/preview' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    id = chatid
                    user = str(msgText).split(' ')[1]
                    jdb.create_user_evea_preview(user,id)
                    jdb.save()
                    msg = 'Ahora @'+user+' está en modo preview'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'》Error en el comando /admin user》')
            else:
                bot.sendMessage(update.message.chat.id,'》No tiene acceso a este comando》')
            return
        if '/ban' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        bot.sendMessage(update.message.chat.id,'⚠️No puede banearse a si mismo⚠️')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '🚫El usuario @'+user+' ah sido baneado del bot!'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'⚠️Error en el comando /ban usuario⚠️')
            else:
                bot.sendMessage(update.message.chat.id,'⚠️No posee permisos de administrador⚠️')
            return
        if '/dameladb' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                sms1 = bot.sendMessage(update.message.chat.id,'Enviando la databse del bot...')
                sms2 = bot.sendMessage(update.message.chat.id,'Base de datos👇🏻:')
                
                bot.editMessageText(sms1,sms2)
                bot.sendFile(update.message.chat.id,'database.jdb')
            else:
                bot.sendMessage(update.message.chat.id,'⚠️No posee permisos de administrador⚠️')
            return
        if '/leerladb' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                database = open('database.jdb','r')
                bot.sendMessage(update.message.chat.id,database.read())
                database.close()
            else:
                bot.sendMessage(update.message.chat.id,'⚠️No posee permisos de administrador⚠️')
            return
        if '/useradm' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                message = bot.sendMessage(update.message.chat.id,'🦾')
                message = bot.sendMessage(update.message.chat.id,'🦾Es administrador del bot así que tiene control total sobre el mismo✅')
            else:
                message = bot.sendMessage(update.message.chat.id,'🙁')
                message = bot.sendMessage(update.message.chat.id,'🙁Usted es solo usuario, por ahora tiene control parcialmente sobre el bot❎')
            return
        # end

        # comandos de usuario
        if '/help' in msgText:
            message = bot.sendMessage(update.message.chat.id,'🙃')
            tuto = open('tuto.txt','r')
            bot.sendMessage(update.message.chat.id,tuto.read())
            tuto.close()
            return
        if '/about' in msgText:
            message = bot.sendMessage(update.message.chat.id,'🤩')
            información = open('información.txt','r')
            bot.sendMessage(update.message.chat.id,información.read())
            información.close()
            return
        if '/commands' in msgText:
            message = bot.sendMessage(update.message.chat.id,'🙂Para añadir estos comandos al menú de acceso rápido debe enviarle el comando /setcommands a @BotFather y luego seleccionar su bot, luego solo queda reenviarle el mensaje con los siguientes comandos y bualah😁.')
            comandos = open('comandos.txt','r')
            bot.sendMessage(update.message.chat.id,comandos.read())
            información.close()
            return
        if '/enable_list' in msgText:
            getUser = user_info
            if getUser:
                getUser['procesos'] = 1
                jdb.save_data_user(username,getUser)
                jdb.save()
                bot.sendMessage(update.message.chat.id, f'》Lista activada')  
            return

        if '/disable_list' in msgText:
            getUser = user_info
            if getUser:
                getUser['procesos'] = 0
                jdb.save_data_user(username,getUser)
                jdb.save()
                bot.sendMessage(update.message.chat.id, f'》Lista desactivada')  
            return

        if '/list' in msgText:
            getUser = user_info
            if getUser:
                bot.sendMessage(update.message.chat.id, f'》Lista:\n\n{len(links)}\n\n/up\n/clear')  
            return

        if '/clear' in msgText:
            getUser = user_info
            if getUser:
                links = []
                bot.sendMessage(update.message.chat.id, f'》 {len(links)} Lista limpiada \n/list')
            return

        if '/up' in msgText:
            url = len(links)
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)

        if '/xdlink' in msgText:
            try: 
                urls = str(msgText).split(' ')[1]
                channelid = getUser['channelid']
                xdlinkdd = xdlink.parse(urls, username)
                msg = f'**Aquí está su link encriptado en xdlink:** `{xdlinkdd}`'
                msgP = f'**Aquí está su link encriptado en xdlink protegido:** `{xdlinkdd}`'
                if channelid == 0:
                    bot.sendMessage(chat_id = chatid, parse_mode = 'Markdown', text = msg)
                else: 
                    bot.sendMessage(chat_id = chatid, parse_mode = 'Markdown', text = msgP)
            except:
                msg = f'》*El comando debe ir acompañado de un link moodle*'
                bot.sendMessage(chat_id = chatid, parse_mode = 'Markdown', text = msg)
            return

        if '/xdon' in msgText:
            getUser = user_info
            if getUser:
                getUser['xdlink'] = 1
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
            return
            
        if '/xdoff' in msgText:
            getUser = user_info
            if getUser:
                getUser['xdlink'] = 0
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
            return

        if '/channelid' in msgText:
            channelId = str(msgText).split(' ')[1]
            getUser = user_info
            try:
                if getUser:
                    getUser['channelid'] = str(msgText).split(' ')[1]
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                msg = f'》*El comando debe ir acompañado de un id de canal*\n\n*Ejemplo: -100XXXXXXXXXX*'
                bot.sendMessage(chat_id = chatid, parse_mode = 'Markdown', text = msg)
            return

        if '/delChannel' in msgText:
            getUser = user_info
            if getUser:
                getUser['channelid'] = 0
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
            return
        if '/myuser' in msgText:
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
                return
        if '/zips' in msgText:
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = '🗜️Perfecto ahora los zips serán de '+ sizeof_fmt(size*1024*1024)+' las partes📚'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'⚠️Error en el comando /zips tamaño de zips⚠️')    
                return
        if '/gen' in msgText:
            pass444
        if '/acc' in msgText:
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'⚠️Error en el comando /acc usuario,contraseña⚠️')
            return

        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'⚠️Error en el comando /host url de la nube⚠️')
            return
        if '/repo' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'⚠️Error en el comando /repo ID de la moodle⚠️')
            return
        if '/xdlink_on' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['xdmode'] = 1
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/xdlink_off' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['xdmode'] = 0
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/cloud' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['cloudtype'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'⚠️Error en el comando /cloud (moodle o cloud⚠️')
            return
        if '/uptype' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'⚠️Error en el comando up tipo de subida (evidence,draft,blog,calendar)⚠️')
            return

        if '/search_proxy' in msgText:
            msg_start = 'Buscando proxy, esto puede tardar...'
            bot.sendMessage(update.message.chat.id,msg_start)
            host = str(update.message.text).split('')[1]
            result = ProxyAuto.Search_ping(host)
            msg = f'**Su nuevo proxy:**\n´{result}´' 
            bot.sendMessage(chat_id = chatid, parse_mode = 'Markdown', text = msg )
            return
        if '/proxy' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    msg = '🧬Perfecto, proxy equipado exitosamente.'
                    bot.sendMessage(update.message.chat.id,msg)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,'🧬Error al equipar proxy.')
            return
        if '/crypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy = S5Crypto.encrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'🧬Proxy encriptado:\n{proxy}')
            return
        if '/decrypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy_de = S5Crypto.decrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'🧬 Proxy desencriptado:\n{proxy_de}')
            return
        if '/off_proxy' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['proxy'] = ''
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    msg = '🧬Bien, proxy desequipado exitosamente.\n'
                    bot.sendMessage(update.message.chat.id,msg)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,'🧬Error al desequipar proxy.')
            return
        if '/view_proxy' in msgText:
            try:
                getUser = user_info
                if getUser:
                    proxy = getUser['proxy']
                    message = bot.sendMessage(update.message.chat.id,'🧬El proxy usado actualmente es:👇🏻')
                    bot.sendMessage(update.message.chat.id,proxy)
            except:
                message = bot.sendMessage(update.message.chat.id,'🧬El proxy usado actualmente es:👇🏻')
                bot.sendMessage(update.message.chat.id,proxy)
            return
        if '/dir' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['dir'] = repoid + '/'
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'⚠️Error en el comando /dir carpeta destino⚠️')
            return
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'🚫𝚃𝙰𝚁𝙴𝙰 𝙲𝙰𝙽𝙲𝙴𝙻𝙰𝙳𝙰🚫')
            except Exception as ex:
                print(str(ex))
            return
        #end

        message = bot.sendMessage(update.message.chat.id,'⏳𝙰𝙽𝙰𝙻𝙸𝚉𝙰𝙽𝙳𝙾...⌛')

        thread.store('msg',message)

        if '/start' in msgText:
            start_msg = '   🌟𝔹𝕆𝕋 𝕀ℕ𝕀ℂ𝕀𝔸𝔻𝕆🌟\n'
            start_msg+= '࿇ ══━━━━✥◈✥━━━━══ ࿇\n'
            start_msg+= '🤖Hola @' + str(username)+'\n'
            start_msg+= '☺️! Bienvenid@ al bot de descargas gratis SuperDownload en su versión inicial 1.0 PlusEdition🌟!\n'
            start_msg+= '🦾Desarrollador: ༺ @Luis_Daniel_Diaz ༻\n\n'
            start_msg+= '🙂Si necesita ayuda o información utilice:\n'
            start_msg+= '/help\n'
            start_msg+= '/about\n'
            start_msg+= '🙂Si usted desea añadir la barra de comandos al menú de acceso rápido de su bot envíe /commands.\n\n'
            start_msg+= '😁𝚀𝚞𝚎 𝚍𝚒𝚜𝚏𝚛𝚞𝚝𝚎 𝚐𝚛𝚊𝚗𝚍𝚎𝚖𝚎𝚗𝚝𝚎 𝚜𝚞 𝚎𝚜𝚝𝚊𝚍𝚒𝚊😁.\n'
            bot.editMessageText(message,start_msg)
            message = bot.sendMessage(update.message.chat.id,'🦾')
        elif '/files' == msgText and user_info['cloudtype']=='moodle':
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 files = client.getEvidences()
                 filesInfo = infos.createFilesMsg(files)
                 bot.editMessageText(message,filesInfo)
                 client.logout()
             else:
                bot.editMessageText(message,'🧐')
                message = bot.sendMessage(update.message.chat.id,'⚠️Error y posibles causas:\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
        elif '/txt_' in msgText and user_info['cloudtype']=='moodle':
             findex = str(msgText).split('_')[1]
             findex = int(findex)
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 evidences = client.getEvidences()
                 evindex = evidences[findex]
                 txtname = evindex['name']+'.txt'
                 sendTxt(txtname,evindex['files'],update,bot)
                 client.logout()
                 bot.editMessageText(message,'𝚃𝚇𝚃 𝙰𝚚𝚞𝚒👇')
             else:
                bot.editMessageText(message,'🧐')
                message = bot.sendMessage(update.message.chat.id,'⚠️Error y posibles causas:\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
             pass
        elif '/token' in msgText:
            message2 = bot.editMessageText(message,'🤖Obteniendo Token, por favor espere🙂...')

            try:
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                      user_info['moodle_password'],
                                      user_info['moodle_host'],
                                      user_info['moodle_repo_id'],proxy=proxy)
                loged = client.login()
                if loged:
                    token = client.userdata
                    modif = token['token']
                    bot.editMessageText(message2,'🤖Su Token es: '+modif)
                    client.logout()
                else:
                    bot.editMessageText(message2,'⚠️La Moodle '+client.path+' no tiene Token⚠️')
            except Exception as ex:
                bot.editMessageText(message2,'⚠️La moodle '+client.path+' no tiene Token o revise la cuenta⚠️')       
        elif '/del_' in msgText and user_info['cloudtype']=='moodle':
            findex = int(str(msgText).split('_')[1])
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                bot.editMessageText(message,'𝙰𝚛𝚌𝚑𝚒𝚟𝚘 𝚎𝚕𝚒𝚖𝚒𝚗𝚊𝚍𝚘🗑️')
            else:
                bot.editMessageText(message,'🧐')
                message = bot.sendMessage(update.message.chat.id,'⚠️Error y posibles causas:\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
        elif '/del_' in msgText and user_info['cloudtype']=='moodle':
            findex = int(str(msgText).split('_')[1])
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                bot.editMessageText(message,'𝙰𝚛𝚌𝚑𝚒𝚟𝚘 𝚎𝚕𝚒𝚖𝚒𝚗𝚊𝚍𝚘🗑️')
            else:
                bot.editMessageText(message,'🧐')
                message = bot.sendMessage(update.message.chat.id,'⚠️Error y posibles causas:\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
        elif 'http' in msgText:
            getUser = user_info
            if int(getUser['procesos']) == 1:  
                links = [msgText]
                updatelinks = json.loads(links) 
                updatelinks.update(links) 
                json.dumps(updatelinks) 
                msg = '》Lista actualizada con éxito'
                bot.sendMessage(update.message.chat.id,msg)
            else:
                url = msgText
                ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
        else:
            #if update:
            #    api_id = os.environ.get('api_id')
            #    api_hash = os.environ.get('api_hash')
            #    bot_token = os.environ.get('bot_token')
            #    
                # set in debug
            #    api_id = 7386053
            #    api_hash = '78d1c032f3aa546ff5176d9ff0e7f341'
            #    bot_token = '5124841893:AAH30p6ljtIzi2oPlaZwBmCfWQ1KelC6KUg'

            #    chat_id = int(update.message.chat.id)
            #    message_id = int(update.message.message_id)
            #    import asyncio
            #    asyncio.run(tlmedia.download_media(api_id,api_hash,bot_token,chat_id,message_id))
            #    return
            bot.editMessageText(message,'⚠️𝙴𝚛𝚛𝚘𝚛, 𝚗𝚘 𝚜𝚎 𝚙𝚞𝚍𝚘 𝚊𝚗𝚊𝚕𝚒𝚣𝚊𝚛 𝚌𝚘𝚛𝚛𝚎𝚌𝚝𝚊𝚖𝚎𝚗𝚝𝚎⚠️')
    except Exception as ex:
           print(str(ex))
  

def main():
    bot_token = os.environ.get('bot_token')
    

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.run()
    asyncio.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()
