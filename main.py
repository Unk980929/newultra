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
import S5Crypto
import cryptocode



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
        bot.editMessageText(message,'》Preparando Para Subir☁...')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],proxy=proxy)
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
                          if user_info['uploadtype'] == 'draft':
                             fileid,resp = client.upload_file_draft(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'perfil':
                             fileid,resp = client.upload_file_perfil(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'blog':
                             fileid,resp = client.upload_file_blog(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'calendar':
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
                bot.editMessageText(message,'》Error En La Pagina》')
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            bot.editMessageText(message,'》Subiendo ☁...')
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
        bot.editMessageText(message,f'》Error {str(ex)}》')


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
    bot.editMessageText(message,'》Preparando Archivo📄...')
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
            if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype'] == 'calendar':
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
    else:
        bot.editMessageText(message,'》Error En La Pagina》')

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
        links = []
        tl_admin_user = os.environ.get('tl_admin_user')

        #set in debug
        tl_admin_user = 'Luis_Daniel_Diaz'

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()
        
        chatid = update.message.chat.id
        id = update.message.chat.id
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
        if '/response' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    chatid = update.message.chat.id
                    chatidd = str(msgText).split(' ')[1]
                    msgs = '<i>Mensaje respondido</i>'
                    bot.sendMessage(chat_id = chatid, parse_mode = 'HTML', text = msgs)
                    mgs = str(msgText).split(maxsplit=2)[2]
                    response = '<i>Nuevo mensaje del admin para usted:</i>\n\n #respuesta \n\n' + mgs
                    bot.sendMessage(chat_id = chatidd, parse_mode = 'HTML', text = response)
                except:
                    bot.sendMessage(update.message.chat.id,'El comando debe estar acompañado del mensaje')
            else:
                bot.sendMessage(update.message.chat.id,'Usted no es admin')
            return 

        if '/add' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    id = chatid
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user,id)
                    jdb.save()
                    msg = 'Ahora @'+user+' tiene acceso al bot temporalmente'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'》Error en el comando /add user》')
            else:
                bot.sendMessage(update.message.chat.id,'》No tiene acceso a este comando》')
            return

        if '/admin' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    id = chatid
                    user = str(msgText).split(' ')[1]
                    jdb.create_admin(user,id)
                    jdb.save()
                    msg = 'Ahora @'+user+' es admin del bot'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'》Error en el comando /admin user》')
            else:
                bot.sendMessage(update.message.chat.id,'》No tiene acceso a este comando》')
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
                        bot.sendMessage(update.message.chat.id,'》Ese usuario es el admin/dev》')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '@'+user+' 》Baneado》'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'》Error en el comando /ban user》')
            else:
                bot.sendMessage(update.message.chat.id,'》No tiene acceso a este comando》')
            return
        if '/gloabl' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    msg = str(msgText).split(maxsplit=1)[1]
                    bot.sendMessage(update.message.chat.id,msg)
                    broadd = broadcast(username)
                    bot.sendMessage(broadd, msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'》El comando /global debe estar acompañado de un mensaje')
            else:
                bot.sendMessage(update.message.chat.id,'》No tiene acceso a este comando》')
            return
        if '/db' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                sms1 = bot.sendMessage(update.message.chat.id,'Enviando la databse del bot...')
                sms2 = bot.sendMessage(update.message.chat.id,'Data del bot:')
                
                bot.editMessageText(sms1,sms2)
                bot.sendFile(update.message.chat.id,'database.jdb')
            else:
                bot.sendMessage(update.message.chat.id,'》No tiene acceso a este comando》')
            return

        # end

        # comandos de usuario
        if '/help' in msgText:
            tuto = open('help.txt','r')
            bot.sendMessage(update.message.chat.id,tuto.read())
            tuto.close()
            return

        if '/about' in msgText:
            bot.sendMessage(update.message.chat.id, f'Soy un bot privado que sube a las moodle de universidades al igual que a las NextCloud.\n\nTodas las cuentas que se configuren el bot, serán temporalmente guardadas en la database de este bot, pero no quiere decir que se roben cuentas, así que con seguridad puedo decir que este bot es seguro para sus cuentas.\n\nDe igual forma, todo está bajo su responsabilidad.\n\nVersión 1.15.0 Basada 7.1')
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

        if '/crypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy = S5Crypto.encrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'Proxy encryptado:\n{proxy}')
            return

        if '/search_proxy' in msgText:
            msg_start = 'Buscando proxy, esto puede tardar...'
            bot.sendMessage(update.message.chat.id,msg_start)
            host = str(update.message.text).split('')[1]
            result = ProxyAuto.Search_ping(host)
            msg = f'**Su nuevo proxy:**\n´{result}´' 
            bot.sendMessage(chat_id = chatid, parse_mode = 'Markdown', text = msg )
            return

        if '/report' in msgText:
            try:
                chatid = update.message.chat.id
                username = update.message.sender.username
                msg = '<i>Reporte enviado con exito al dev!</i>'
                bot.sendMessage(chat_id = chatid, parse_mode = 'HTML', text = msg)
                mgs = str(msgText).split(maxsplit=1)[1]
                report = '#reporte ' + mgs + f'\n\n_Reporte enviado por {username} ID: _`{chatid}`' 
                bot.sendMessage(chat_id = 1166737705, parse_mode = 'Markdown', text = report)
            except:
                bot.sendMessage(update.message.chat.id,'El comando debe estar acompañado del reporte')
            return 

        if '/decrypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy_de = S5Crypto.decrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'Proxy decryptado:\n{proxy_de}')
            return

        if '/my' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
                getUser = user_info
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
                return
        if '/zip' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
                getUser = user_info
                if getUser:
                    try:
                        size = int(str(msgText).split(' ')[1])
                        getUser['zips'] = size
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        msg = 'Ahora los zips seran de '+ sizeof_fmt(size*1024*1024) +'\n'
                        msg+= 'Añadiendo a la configuración...\n'
                        bot.sendMessage(update.message.chat.id,msg)
                        statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                    except:
                        bot.sendMessage(update.message.chat.id,f'》Error en el comando /zip size')
                return
        if '/acc' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
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
                    bot.sendMessage(update.message.chat.id,'》Error en el comando /acc user,password')
            return
        if '/host' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
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
                    bot.sendMessage(update.message.chat.id,'》Error en el comando /host moodlehost')
            return
        if '/repo' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
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
                    bot.sendMessage(update.message.chat.id,'》Error en el comando /repo id')
            return
        if '/token_on' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
                try:
                    getUser = user_info
                    if getUser:
                        getUser['tokenize'] = 1
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                except:
                    bot.sendMessage(update.message.chat.id,'》Error en el comando /tokenize state')
            return
        if '/token_off' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
                try:
                    getUser = user_info
                    if getUser:
                        getUser['tokenize'] = 0
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                except:
                    bot.sendMessage(update.message.chat.id,'》Error en el comando /tokenize state')
            return
        if '/cloud' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
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
                    bot.sendMessage(update.message.chat.id,'》Error en el comando /cloud (moodle o cloud)')
            return
        if '/uptype' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
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
                    bot.sendMessage(update.message.chat.id,'》Error en el comando /uptype (typo de subida (evidence,draft,blog,calendar,perfil))》')
            return
        if '/proxy' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
                try:
                    cmd = str(msgText).split(' ',2)
                    proxy = cmd[1]
                    getUser = user_info
                    if getUser:
                        getUser['proxy'] = proxy
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
                except:
                    if user_info:
                        user_info['proxy'] = ''
                        statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                        bot.sendMessage(update.message.chat.id,statInfo)
            return

        if '/resetxy' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
                reset = ''
                getUser = user_info
                if getUser:
                    getUser['proxy'] = reset
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            return

        if '/dir' in msgText:
            preview = jdb.preview(username)
            if preview:
                bot.sendMessage(update.message.chat.id, f'》Usted está en modo preview')
            else:
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
                    bot.sendMessage(update.message.chat.id,'》Error en el comando /dir folder')
            return
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'》Descarga Cancelada')
            except Exception as ex:
                print(str(ex))
            return
        #end

        message = bot.sendMessage(update.message.chat.id,'》Analizando...')
        getUser = user_info
        thread.store('msg',message)

        if '/start' in msgText:
            chat_id = update.message.chat.id
            getUser = user_info
            if getUser:
                getUser['broadcast'] = chat_id
                jdb.save_data_user(username,getUser)
                jdb.save()
            print(f'El bot se a activado por: {username}')
            msg = 'Bienvenido a TgUploader en su versió 1.20.0!\n\n'
            msg+= 'Para saber como funciona esta versión solo use: /help\n'
            bot.editMessageText(message,msg)
        elif '/files' == msgText and user_info['cloudtype']=='moodle':
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)                     
            loged = client.login()
            if loged:
                List = client.getEvidences()
                List1=List[:45]
                total=len(List)
                List2=List[46:]
                info1 = f'<b>Archivos: {str(total)}</b>\nEliminar todo: /del_all\n\n'
                info = f'<b>Archivos: {str(total)}</b>\nEliminar todo: /del_all\n\n'
                
                i = 1
                for item in List1:
                    info += '<b>/del_'+str(i)+'</b>\n'
                    #info += '<b>'+item['name']+':</b>\n'
                    for file in item['files']:                  
                        info += '<a href="'+file['directurl']+'">\t'+file['name']+'</a>\n'
                    info+='\n'
                    i+=1
                    bot.editMessageText(message, f'{info}',parse_mode="html")
                
                if len(List2)>0:
                    bot.sendMessage(update.message.chat.id,'Conectando con Lista número 2...')
                    for item in List2:
                        
                        info1 += '<b>/del_'+str(i)+'</b>\n'
                        #info1 += '<b>'+item['name']+':</b>\n'
                        for file in item['files']:                  
                            info1 += '<a href="'+file['url']+'">\t'+file['name']+'</a>\n'
                        info1+='\n'
                        i+=1
                        bot.editMessageText(message, f'{info1}',parse_mode="html")
            else:
                bot.editMessageText(message,'》Error y posibles causas:\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
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
                 bot.editMessageText(message,'TxT Aqui')
             else:
                bot.editMessageText(message,'》Error y posibles causas:\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
             pass
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
                bot.editMessageText(message,'Archivo Borrado')
            else:
                bot.editMessageText(message,'》Error y posibles causas:\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
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
            if update:
                api_id = os.environ.get('api_id')
                api_hash = os.environ.get('api_hash')
                bot_token = os.environ.get('bot_token')
                
                api_id = 11639974
                api_hash = 'a5007babf6f3e96c9b51564356b64c30'
                bot_token = '5381132814:AAHrmCxn16uzPnUav7MCd1N-J5rFp65GS0s'

                chat_id = update.message.chat.id
                message_id = update.message.message_id
                import asyncio
                asyncio.run(tlmedia.download_media(api_id,api_hash,bot_token,chat_id,message_id))
                return
            bot.editMessageText(message,'No se pudo analizar correctamente')
    except Exception as ex:
           print(str(ex))


def main():
    bot_token = os.environ.get('bot_token')

    #set in debug
    bot_token = '5381132814:AAHrmCxn16uzPnUav7MCd1N-J5rFp65GS0s'

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.run()

if __name__ == '__main__':
    try:
        print(update.message.chat.id)
        main()
    except:
        main()
