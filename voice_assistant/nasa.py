
# import requests 
# import os 
# from PIL import Image 
# import pyttsx3 
# import matplotlib.pyplot as plt 
# import cartopy.crs as ccrs 
# import datetime  
# import random 
# api_key="XNN3qHB7sIu5egaoKKBcUhJ4aM4yGodEHLBYfHnh" 
 
# def Summary(body): 
#     value=str(random.randrange(1,16)) 
#     if '1' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\1.jpeg") 
#     elif '2' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\2.jpeg") 
#     elif '3' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\3.jpeg") 
#     elif '4' in value: 
#         os.startfile("C:C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\4.jpeg") 
#     elif '5' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\5.jpeg") 
#     elif '6' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\6.jpeg") 
#     elif '7' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\7.jpeg") 
#     elif '8' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\.jpeg") 
#     elif '9' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\9.jpeg") 
#     elif '10' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\10.jpeg") 
#     elif '11' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\11.jpeg") 
#     elif '12' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\12.jpeg") 
#     elif '13' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\13.jpeg") 
#     elif '14' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\14.jpg") 
#     elif '15' in value: 
#         os.startfile("C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\images_used\\15.jpg") 
     
#     name = str(body) 
#     url = "http://hubblesite.org/api/v3/features/"+str(name) 
     
#     r=requests.get(url) 
#     data=r.json() 
#     if len(data) != 0: 
#         info = data['defination'] 
#         speak(f'according to my database : {info}') 
#     else: 
#         speak("No data available , Try Again later") 
     
     
# engine= pyttsx3.init('sapi5') 
# voices= engine.getProperty('voices') 
# engine.setProperty('voices',voices[1].id) 
# engine.setProperty('rate',170) 
# def speak(audio): 
#     print("   ") 
#     print(f":  {audio}") 
#     print("   ") 
#     engine.say(audio) 
#     engine.runAndWait()   
# def NasaNews(date): 
     
#             url = "http://api.nasa.gov/planetary/apod?api_key=" + str(api_key) 
#             Para = {'date':str(date)} 
#             r=requests.get(url,params = Para) 
#             data = r.json() 
#             info = data['explanation'] 
#             title =data['title'] 
             
#             Img_url=data['url'] 
#             image_r = requests.get(Img_url) 
#             FileName = str(date)+'.jpg' 
#             with open(FileName,'wb') as f: 
#                 f.write(image_r.content) 
#             path1="C:\\Users\\abc\\Desktop\\MY AI PROJECT\\"+str(FileName) 
#             path2="C:\\Users\\abc\\Desktop\\MY AI 
# PROJECT\\DATABASE\\NASA\\img_space\\"+str(FileName) 
#             os.rename(path1,path2) 
#             img=Image.open(path2) 
#             img.show() 
#             speak(title) 
#             speak(f"According to nasa:{info}") 
 
# def mars(): 
#     name='curiosity' 
#     date = '2020-12-3' 
     
#     api="2WbrclsQaBuGd75awgpZhonwK5cKSKRjQkxZasJQ" 
#     api_ = str(api) 
#     url 
# =f"https://api.nasa.gov/mars-photos/api/v1/rovers/{name}/photos?earth_date{date}&api_key{api}" 
#     print(url) 
     
# def isstracker(): 
#     url = "http://api.open-notify.org/iss-now.json" 
#     r=requests.get(url) 
#     data=r.json() 
#     dt=data['timestamp'] 
#     lat = data['iss_position']['latitude'] 
#     long = data['iss_position']['longitude'] 
#     print(f"time and date:{dt}") 
#     print(f"latitude:{lat}") 
#     print(f"longitude:{long}") 
#     plt.figure() 
#     ax=plt.axes(projection = ccrs.PlateCarree()) 
#     ax.stock_img() 
#     plt.scatter(float(long),float(lat),color = 'blue',marker = ".") 
#     plt.show() 
# def Astro(start_date,end_date): 
#     url 
# =f"http://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_
#  key}" 
#     try: 
#         r=requests.get(url) 
#         Data=r.json() 
#         tb=Data['element_count'] 
         
#         print(tb) 
#         neo =Data['near_earth_objects'] 
#         speak(f"Total asteroid betweer {start_date} and {end_date} is :{tb}") 
#         for body in neo[start_date]: 
#             id = body['id'] 
#             name = body['name'] 
#             absolute =body['absolute_magnitude_h'] 
#             print(id,name,absolute) 
#     except: 
#         speak("Date gap is very large") 
# def astrobody(body): 
#     url=f"https://api.le-systeme-solaire.net/rest/bodies/"+str(body) 
#     rrr = requests.get(url) 
#     data=rrr.json() 
#     number=len(data) 
#     mass=data['mass']['massValue'] 
#     volume = data['vol']['volValue'] 
#     density = data['density'] 
#     gravity = data['gravity'] 
#     escapev = data['escape'] 
#     speak(f"number of bodies : {number} ") 
#     speak(f"Mass of {body} : {mass} M☉") 
#     speak(f"volume of {body} : {volume}AU ") 
#     speak(f"density of {body} : {density}km3 ") 
#     speak(f"gravity of {body} : {gravity} ") 
#     speak(f"Escape Velocity of {body} : {escapev}m/s ") 
#     astrobody("earth")