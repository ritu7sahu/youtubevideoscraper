from flask import Flask, render_template, request,jsonify
import time
import os
import glob
import shutil
from flask_cors import cross_origin
from selenium import webdriver
from selenium.common import exceptions
from pytube import YouTube
import boto3
import json
from botocore.exceptions import NoCredentialsError
#import mysql.connector as connection
import pandas as pd
import pymongo

# ("getting access key & secret key of aws s3")
ACCESS_KEY = 'AKIAXYJ4NMAJS5RLMMX5'
SECRET_KEY = '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'
# ("connecting mysql and mongodb")

try:
    # mydb = connection.connect(host="localhost", user="root", password="Root@123")
    # cursor = mydb.cursor()
    client = pymongo.MongoClient("mongodb+srv://ritusahu:ritusahupwd@cluster0.telj5.mongodb.net/?retryWrites=true&w=majority")
except Exception as e:
    print(e)

app = Flask(__name__)
# ("route to display the home page")
@app.route('/', methods=['GET'])
@cross_origin()
def homePage():
    return render_template("index.html")

# ("route to display the Youtuber details page")
@app.route('/result', methods=['POST', 'GET'])  # route to show the review comments in a web UI
@cross_origin()
def index():
    if request.method == 'POST':
        # ("getting url from form after clicking on search button")
        url = request.form['content']
        videos_in_no = request.form['no_of_videos']
        driver_path = r'https://github.com/ritu7sahu/youtubevideoscraper/blob/cebb8aecbe188deba9a8053f5dd8e6061aee2c92/chromedriver.exe'
        driver = webdriver.Chrome(executable_path = driver_path)
        # ("creating driver and accessing url in Chrome")
        driver.get(url)
        # ("Calling function to getAllVideosLinks")
        links = getVideosLinks(driver,videos_in_no)
        # ("Calling function getAllDetails() to get All Youtuber & comments details ")

        getAllDetails(links,driver)
        # ("Calling function databaseRelated() to process insert details into database  ")
        databaseRelated()
        # ("Calling function getAllDataFromDB() to get all details from database  ")
        data = getAllDataFromDB()
        driver.close()
        # ('Rendering details data to Youtuber details Page')
        return render_template("results.html",data=jsonify(data['details']))


    else:
        return render_template("index.html")

# ("route to display the comments page")
@app.route('/get_comments', methods=['POST', 'GET'])  # route to show the review comments in a web UI
@cross_origin()

def get_comments():
    if request.method == 'POST':
        try:
            link = request.form['link']
            database = client['youtubeData']
            collection = database['youtuberCommentsDetails']
            # ("getting all comments from link")
            comments = collection.find({'yt_link':link})
            # ("rendering comments page to show all comments")
        except Exception as e:
            print(e)
        return render_template("comments.html", data=jsonify(comments))


def getAllDataFromDB():
    # ("getting all youtuber details from database")
    try:
        database = client['youtubeData']
        collection = database['youtuberscraperdata']
        # ("getting all comments from link")
        yt_details = collection.find()
    except Exception as e:
        print(e)
    return {'details':yt_details}

def getVideosLinks(driver,videos_in_no):
    # ("started function to get all videos links ")
    try:
        content_section = driver.find_element_by_xpath('//*[@id="contents"]')
        driver.execute_script("arguments[0].scrollIntoView();", content_section)
        time.sleep(7)
        # ("Scroll all the way down to the bottom in order to get all the.")
        last_height = driver.execute_script("return document.documentElement.scrollHeight")

        while True:
            # ("Scroll down 'til next load")
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")

            # ("Wait to load everything thus far.")
            time.sleep(2)

            # ("Calculate new scroll height and compare with last scroll height.")
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # ("One last scroll just in case.")
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
    except Exception as e:
        print(e)
    yt_urls = set()
    link_count = 0
    max_links_to_fetch = int(videos_in_no)
    try:
        # ("checking while link count is less than max link to fetch")
        while link_count < max_links_to_fetch:
            driver.execute_script("return document.documentElement.scrollHeight")
            time.sleep(4)
            links = driver.find_elements_by_xpath('//*[@id="thumbnail"]')

            for link in links:
                # ("try to click every link")

                # ("add links one by one to yt_urls")
                if link.get_attribute('href') and 'https' in link.get_attribute('href'):
                    data = link.get_attribute('href')
                    if 'shorts' in data:
                        continue
                    else:
                        yt_urls.add(link.get_attribute('href'))

                link_count = len(yt_urls)

                if len(yt_urls) >= max_links_to_fetch:
                    print(f"Found: {len(yt_urls)} links, done!")
                    break
            else:
                print("Found:", len(yt_urls), "links, looking for more ...")
                time.sleep(5)
                return
    except Exception as e:
        print(e)
    # ("Returning all url links")
    return yt_urls

comment_section=''
channel=''
no_of_comments=''
likes=''
def getAllDetails(links, driver):
    # ("Started getAll details function")
    # ("Created 2 list for yt info and comments")
    yt_info = []
    commentsDetails = []
    i=1
    boolVal = True
    # ("Iterating links one by one")

    for link in links:

        #global channel
        driver.get(link)
        #driver.maximize_window()
        time.sleep(7)

        comment_section = driver.find_element_by_xpath('//*[@id="comments"]')
        driver.execute_script("arguments[0].scrollIntoView();", comment_section)
        time.sleep(7)
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        # ("code for taking all comments after scrolling page till end")
        while True:
            # Scroll down 'til "next load".
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            # Wait to load everything thus far.
            time.sleep(2)
            # Calculate new scroll height and compare with last scroll height.
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        # One last scroll just in case.
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        try:
            # Extract the elements storing the usernames and comments.
            username_elems = driver.find_elements_by_xpath('//*[@id="author-text"]')
            comment_elems = driver.find_elements_by_xpath('//*[@id="content-text"]')

        except exceptions.NoSuchElementException:
            error = "Error: Double check selector OR "
            error += "element may not yet be on the screen at the time of the find operation"

        try:
        # ("Extract the elements storing the video title and comment section.")
            yt = YouTube(link)
            title = yt.title
            yt_link = driver.current_url
            v_id = yt_link.split('v=')[1]
            no_of_comments = driver.find_element_by_xpath('//*[@id="count"]/yt-formatted-string').text
            thumbnail_link = 'https://img.youtube.com/vi/' + v_id + '/maxresdefault.jpg'
            channel = driver.find_element_by_xpath('//*[@id="text"]/a').text




        except exceptions.NoSuchElementException:
            error = "Error: Double check selector OR "
            error += "element may not yet be on the screen at the time of the find operation"
            print(error)

        if (boolVal == True):
            try:
                dir = 'G:/videos/' + (channel.replace(" ", "")).lower() + "/"
                if os.path.exists(dir):
                    shutil.rmtree(dir)
            except Exception as e:
                print(e)
        boolVal = False
        # ("Calling function to download videos from link to local storage drive G:")

        downloaded_video_path = downloadVideo(link,i,title,channel)
        # ("Calling function to upload videos to aws s3 bucket")
        aws_link = upload_to_aws(downloaded_video_path,channel)
        i+=1
        likes = driver.find_element_by_css_selector("#top-level-buttons-computed  yt-formatted-string").text
        list_basic = [channel,yt_link,downloaded_video_path ,aws_link, likes,no_of_comments, title]
        # ("Adding all youtuber details & comments in list ")
        yt_info.append(list_basic)
        for username, comment in zip(username_elems, comment_elems):
            commentsDetails.append([channel,yt_link,username.text, comment.text,thumbnail_link])

        # ("checking if csv file exists for comments and yt details ")
        if os.path.exists("comments.csv"):
            os.remove("comments.csv")
        else:
            print("The file does not exist")

        # ("creating dataframe for comments and converted list data to csv file")
        cmts = pd.DataFrame(commentsDetails,columns=['youtuber_name','yt_link','commenter_name', 'comments','thumbnail_link'])
        cmts.to_csv('comments.csv', index=False, header=['youtuber_name','yt_link','commenter_name', 'comments','thumbnail_link'])

        if os.path.exists("youtuberInfo.csv"):
            os.remove("youtuberInfo.csv")
        else:
            print("The file does not exist")
        # ("creating dataframe for youtuber details and converted list data to csv file")
        basic_info = pd.DataFrame(yt_info)
        basic_info.to_csv('youtuberInfo.csv', index=False, header=['channel','yt_link','downloaded_video_path' ,'aws_link', 'likes','no_of_comments', 'title'])
    # ("returning youtuber info and comments details in dictionary form")
    return {'yt_info':yt_info,'comments':commentsDetails}

def downloadVideo(link,i,title,channel):
    # ("Code started for downloding video")
    try:
        DOWNLOAD_PATH = 'G:/videos/'+(channel.replace(" ", "")).lower()+"/"
        if not os.path.exists(DOWNLOAD_PATH):
            os.makedirs(DOWNLOAD_PATH)
        yt = YouTube(link)

        file = DOWNLOAD_PATH+title+'.mp4'
        if not os.path.exists(file):
            pass
        else:
            os.remove(file)
        mp4_files = yt.streams.filter(file_extension="mp4")
        mp4_369p_files = mp4_files.get_by_resolution("360p")
        mp4_369p_files.download(DOWNLOAD_PATH)
        list_of_files = glob.glob(DOWNLOAD_PATH+"*")  # * means all
        file = max(list_of_files, key=os.path.getctime)
        latestFile = os.path.join(DOWNLOAD_PATH, file)
        # ("Calling rename function to rename the files")
        newFile = renameFile(latestFile,i,DOWNLOAD_PATH)
    except Exception as e:
        print(e)
    return newFile

def renameFile(file,i,dir_path):
    # ("Rename file function started")
    new_filename = 'video'+str(i)+'.mp4'
    old_filename = file
    if not os.path.exists(new_filename):
        pass
    else:
        os.remove(new_filename)
    os.rename(old_filename,os.path.join(dir_path,new_filename))
    # ("returns renamed file")
    return os.path.join(dir_path,new_filename)

def upload_to_aws(file,channel):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)
    arr = file.split('/')
    filename = (channel.replace(" ", "")).lower() + "/"+arr[3]

    try:
        s3.upload_file(file, 'videos-bucket-50', filename)
        link = 'https://videos-bucket-50.s3.ap-south-1.amazonaws.com/' + filename

        # ("Upload Successful")
        return link
    except FileNotFoundError:
        # ("The file was not found")
        return False
    except NoCredentialsError:
        # ("Credentials not available")
        return False


def databaseRelated():
    # ("creating database & table")
    try:
        # cursor.execute('CREATE DATABASE IF NOT EXISTS youtubeScraper')
        # # ("creating tables")
        # yt_info = 'create table if not exists youtubeScraper.youtuberscraperdata( youtuber_name varchar(50),video_link varchar(50),downloaded_video_path varchar(50),aws_link varchar(100),likes varchar(20),no_of_comments varchar(20),title varchar(100))'
        # cursor.execute(yt_info)
        cwd = os.getcwd()+"\youtuberInfo.csv"
        yt_df = pd.read_csv(cwd)
        payload_yt = json.loads(yt_df.to_json(orient='records'))
        database = client['youtubeData']
        collection1 = database['youtuberscraperdata']
        # ("Iterating dataframe & inserting comments record in mongodb")
        for data in payload_yt:
            get = collection1.count_documents({'video_link': data['yt_link']})
            if (get == 0):
                collection1.insert_one(data)
            else:
                pass

        # ("Iterating dataframe & inserting records in mysql")
        # for (rows, rs) in yt_df.iterrows():
        #     # ("Checking for duplicate records")
        #     record = 'select count(*) as count from youtubeScraper.youtuberscraperdata where video_link ="' + str(
        #         rs[1]) + '"'
        #     cursor.execute(record)
        #     rowcount = cursor.fetchone()[0]
        #     if (rowcount > 0):
        #         continue
        #     else:
        #         # qry = "insert into youtubeScraper.youtuberscraperdata values(""'" + str(rs[0]) + "','" + str(
        #         # rs[1]) + "','" + str(rs[2]) + "','" + str(rs[3]) + "','" + str(rs[4]) + "','" + str(
        #         # rs[5]) + "','" + str(rs[6]) + "')"
        #
        #         qry = 'insert into youtubeScraper.youtuberscraperdata values(''"' + str(rs[0]) + '","'+ str(
        #             rs[1]) + '","' + str(rs[2]) + '","' + str(rs[3]) + '","' + str(rs[4]) + '","' + str(
        #             rs[5]) + '","' + str(rs[6]) + '")'
        #         print(qry)
        #         cursor.execute(qry)
        #         mydb.commit()
        # ("data inserted")
        csv_path = os.getcwd() + "\comments.csv"
        # yt_df = pd.read_csv(cwd)
        data1 = pd.read_csv(csv_path)
        payload = json.loads(data1.to_json(orient='records'))
        database = client['youtubeData']
        collection = database['youtuberCommentsDetails']
        # ("Iterating dataframe & inserting comments record in mongodb")
        for data in payload:
            get = collection.count_documents({'yt_link': data['yt_link'], 'commenter_name': data['commenter_name'], 'comments': data['comments']})
            if (get == 0):
                collection.insert_one(data)
            else:
                pass

    except Exception as e:
        print(e)

if __name__ == "__main__":
    #app.run(host='127.0.0.1', port=8001, debug=True)
	app.run(debug=True)