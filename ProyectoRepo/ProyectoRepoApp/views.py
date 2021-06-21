from django import http
from django.http import HttpRequest
from django.http import HttpResponse
from django.template import Template, Context
from django.template import loader
from django.shortcuts import render 
from django.conf import settings

from bs4 import BeautifulSoup
import urllib.request
import lxml
from datetime import datetime


def obtener_soup(web_url):
    user_agent ='Mozilla/5.0'
    headers={'User-Agent':user_agent} 
    request=urllib.request.Request(web_url,None,headers)
    page = urllib.request.urlopen(request).read()
    
    soup = BeautifulSoup(page, "lxml-xml")
    return soup

def consulta_oai(url_base, ListRecord = False ,GetRecord =False, identifier = None, sfrom = None, metadataPrefix = None):
    '''Recibe una url_base de un repositorio. se arma las consultas segun el protocolo oai-pmh y los parametros que son recibidos'''
    
    if GetRecord and not identifier: #termina la ejecucion 
        raise RuntimeError("Para un getRecord, necesito identificador.") 
    consulta = url_base + '?verb='#empieza la consulta
    lista = []#se almacenan los parametros usados para la consulta 
    
    #verbs ListRecord. GetRecord
    if ListRecord:
        lista.append('ListRecords')#con ListRecord se obtienen los encabezados de los registros. De aqui sacamos los indentificadores de cada registro
    if GetRecord:
        lista.append(f'GetRecord')
        lista.append(f'identifier={identifier}')
    
    if sfrom:
        lista.append(f'from={sfrom}')#es un parametro opcional
    if metadataPrefix:
        lista.append(f'metadataPrefix={metadataPrefix}')#el repositorio tiene que usar dublin core como tipo de metadato. Es obligatorio
    
    agregar = '&'.join(lista)    
    consulta += agregar
    xml_soup = obtener_soup(consulta)
    return xml_soup

def buscar_registros(registros,url_base):
    list_titulos = []
    list_autores = []
    list_colab = []
    list_resumen = []
    list_palabras= []
    list_fecha = []
    list_link = []

    for id_registro in registros:
        xml_GetRecord = consulta_oai(url_base, GetRecord=True, identifier=id_registro,metadataPrefix = 'oai_dc' )
        
        titulo = xml_GetRecord.find('dc:title').text
        
        autor = xml_GetRecord.find('dc:creator').text
        
        colaboradores = [colaborador.text for colaborador in xml_GetRecord.find_all('dc:contributor')] 
        try:
            resumen = xml_GetRecord.find('dc:description').text 
        except AttributeError as e:
            continue
        
        palabras_clave = [palabra.text for palabra in xml_GetRecord.find_all('dc:subject')]
        
        etiq_date = [fecha.text for fecha in xml_GetRecord.find_all('dc:date')]
        for fecha in etiq_date:
            try:
                date_object = datetime.strptime(fecha, "%Y-%m-%dT%H:%M:%SZ")
                fecha = date_object.strftime('%d/%m/%Y') #('%d/%m/%Y, %H:%M:%S')
            except ValueError as e:
                    continue
        etiq_iden = [link.text for link in xml_GetRecord.find_all('dc:identifier')]
        for enlace in etiq_iden:
            if 'handle'in enlace:
                entrada = enlace
            else:
                entrada="No tiene"
        
        list_autores.append(autor)
        list_colab.append(colaboradores)
        list_titulos.append(titulo)
        list_resumen.append(resumen)
        list_palabras.append(palabras_clave)
        list_fecha.append(fecha)
        list_link.append(entrada)
    lista_final = zip(registros,list_autores,list_colab,list_titulos, list_resumen, list_palabras, list_fecha, list_link)
    return list(lista_final)

lista_registros =[]

def home(request): #Esta es la funcion que llama la url
    global lista_registros

    if request.method =="POST":
        url=request.POST['url']
        lista_registros = []
        xml_ListRecord = consulta_oai(url, ListRecord=True, sfrom = '2021-01-01', metadataPrefix = 'oai_dc')
        registros = [ iden.text for iden in xml_ListRecord.find_all('identifier') if 'http' not in iden.text and 'oai' in iden.text]
        lista_registros = buscar_registros(registros,url)
        return render(request, "index.html",{'lista':lista_registros})

    return render(request,'index.html')

def registro(request,pk):
    valor = pk - 1
    elemento = lista_registros[valor]
    #print(elemento)
    return render(request,'registro.html',{'registro':elemento})



