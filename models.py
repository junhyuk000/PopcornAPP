import mysql.connector
from datetime import datetime
from flask import flash
import pymysql
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import pandas as pd
import json



class DBManager:
    def __init__(self):
        # MySQL 데이터베이스 연결
        self.connection = None
        self.cursor = None
        
    def connect(self):
        
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                host='10.0.66.20',
                user='sejong',
                password='1234',
                database='movie_db',
                connection_timeout=600  # 10분
                )
                self.cursor = self.connection.cursor(dictionary=True)
                self.cursor.execute("""
                                    CREATE TABLE IF NOT EXISTS `posts` (
                                    `id` INT(11) NOT NULL AUTO_INCREMENT,
                                    `userid` VARCHAR(255) NOT NULL,
                                    `username` VARCHAR(255) NOT NULL,
                                    `title` VARCHAR(200) NOT NULL,
                                    `content` TEXT NOT NULL,
                                    `rating` INT(11) NOT NULL,
                                    `spoiler` BOOLEAN NOT NULL,
                                    `filename` VARCHAR(255) DEFAULT NULL,
                                    `movie_title` VARCHAR(255) DEFAULT NULL,
                                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP(),
                                    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),
                                    `views` INT(11) DEFAULT 0,

                                    PRIMARY KEY (`id`)
                                    )
                                    """)
            
                self.cursor.execute("""
                                    CREATE TABLE IF NOT EXISTS `users` (
                                    `idx` INT(11) NOT NULL AUTO_INCREMENT,
                                    `id` VARCHAR(255) NOT NULL,
                                    `name` VARCHAR(255) NOT NULL,
                                    `password` VARCHAR(255) NOT NULL,
                                    `user_ip` VARCHAR(45) NOT NULL,
                                    `filename` VARCHAR(255) DEFAULT NULL,
                                    `reg_date` DATETIME DEFAULT CURRENT_TIMESTAMP(),
                                    PRIMARY KEY (`idx`)
                                    ) 
                                    """)

                self.cursor.execute("""
                                    CREATE TABLE IF NOT EXISTS `movies` (
                                    `id` INT(11) NOT NULL AUTO_INCREMENT,
                                    `rank` INT(11) NOT NULL,
                                    `title` VARCHAR(255) NOT NULL,
                                    `genres` VARCHAR(255) NOT NULL,
                                    `director` VARCHAR(200) NOT NULL,
                                    `nations`VARCHAR(200) NOT NULL,
                                    `t_audience` BIGINT NOT NULL,
                                    `c_audience` BIGINT NOT NULL,
                                    `t_sales` BIGINT NOT NULL,
                                    `c_sales` BIGINT NOT NULL,
                                    `filename` VARCHAR(255) NOT NULL DEFAULT 'noimage.jpg',
                                    `release_date` DATETIME NOT NULL,
                                    `input_date` DATETIME DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),

                                    PRIMARY KEY (`id`)
                                    )
                                    """)

                self.cursor.execute("""
                                    CREATE TABLE IF NOT EXISTS `movies_info` (
                                    `id` INT(11) NOT NULL AUTO_INCREMENT,
                                    `rank` INT(11) NOT NULL,
                                    `title` VARCHAR(255) NOT NULL,
                                    `genres` VARCHAR(255) NOT NULL,
                                    `director` VARCHAR(200) NOT NULL,
                                    `nations`VARCHAR(200) NOT NULL,
                                    `t_audience` BIGINT NOT NULL,
                                    `c_audience` BIGINT NOT NULL,
                                    `t_sales` BIGINT NOT NULL,
                                    `c_sales` BIGINT NOT NULL,
                                    `filename` VARCHAR(255) NOT NULL DEFAULT 'noimage.jpg',
                                    `release_date` DATETIME NOT NULL,
                                    `input_date` DATETIME DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),

                                    PRIMARY KEY (`id`)
                                    )
                                    """)
            self.cursor = self.connection.cursor(dictionary=True)
        except mysql.connector.Error as error:
            print(f"데이터베이스 연결 실패: {error}")
            
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
#--------------------------기본값으로 설정--------------------------------★    
    def get_all_posts(self):
        try:
            self.connect()
            sql = f"SELECT * FROM posts order by views desc"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except mysql.connector.Error as error:
            print(f"게시글 조회 실패: {error}")
            return []
        finally:
            self.disconnect()
            
    def insert_post(self, title, content, filename, userid, username, rating, spoiler, movie_title):
        try:
            self.connect()
            sql = f"INSERT INTO posts (title, content, filename, created_at, userid, username, rating, spoiler,movie_title) values (%s, %s, %s, %s, %s, %s, %s, %s,%s)"
            values = (title, content, filename, datetime.now(), userid, username, rating, spoiler, movie_title)  # 튜플형태
            self.cursor.execute(sql, values)
            
            '''
            ##  executemany() : list로 묶어서 한번에 입력 가능
            values = [(title, content, filename, datetime.now().date().strftime('%Y-%m-%d')),(title, content, filename, datetime.now().date().strftime('%Y-%m-%d'))]
            self.cursor.executemany(sql, values)
            '''
            
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            print(f"게시글 추가 실패: {error}")
            return False
        finally:
            self.disconnect()
            
    def get_post_by_id(self, id):
        try:
            self.connect()
            sql = f"SELECT * FROM posts WHERE id = %s"
            value = (id,) # 튜플에 값이 한개만 들어갈때 ,해줘야됨 
            self.cursor.execute(sql, value)
            return self.cursor.fetchone()
        except mysql.connector.Error as error:
            print(f"데이터베이스 연결 실패: {error}")
            return None
        finally:
            self.disconnect()
            
    def update_post(self, id, title, content, filename):
        try:
            self.connect()
            if filename:
                sql = f"UPDATE posts SET title = %s, content =%s, filename= %s WHERE id =%s"
                values = (title, content, filename, id)  # 튜플형태
            else:
                sql = f"UPDATE posts SET title = %s, content =%s WHERE id =%s"
                values = (title, content, id)  # 튜플형태
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"게시글 정보 수정 실패: {error}")
            return False
        finally:
            self.disconnect()
            
    def delete_post(self, id):
        try:
            self.connect()
            sql = f"DELETE FROM posts WHERE id = %s"
            value = (id,) # 튜플에 값이 한개만 들어갈때 ,해줘야됨 
            self.cursor.execute(sql, value)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            print(f"게시글 삭제 실패: {error}")
            return False
        finally:
            self.disconnect()
            
    def increment_hits(self, id):
        try:
            self.connect()
            sql = f"UPDATE posts SET views = views +1 WHERE id = %s"
            value = (id,) # 튜플에 값이 한개만 들어갈때 ,해줘야됨 
            self.cursor.execute(sql, value)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            print(f"게시글 조회수 증가 실패: {error}")
            return False
        finally:
            self.disconnect()        
        
            
    def regsiter_user(self, name, id, password,user_ip, filename):
        try:
            self.connect()
            sql = f"INSERT INTO users (name, id, password, user_ip,filename) values (%s, %s, password(%s),%s, %s)"
            values = (name, id, password, user_ip,filename)  # 튜플형태
            self.cursor.execute(sql, values)

            self.connection.commit()

            flash("계정등록이 성공적으로 완료되었습니다!", "success")
            return True
        except mysql.connector.Error as error:
        # except pymysql.IntegrityError as e:    
            print(f"계정 등록 실패: {error}")
            # flash("중복된 아이디가 존재 합니다.", "error")
            return False
        finally:  
            self.disconnect() 
    
    def login_user(self, id, password):
        try:
            self.connect()
            sql = f"SELECT * FROM users where id = %s and password=password(%s)"
            values = (id, password)
            self.cursor.execute(sql,values)
            return self.cursor.fetchone()
        except mysql.connector.Error as error:
            flash("계정 조회 실패", "error")
            print(f"계정 조회 실패: {error}")
            return []
        finally:
            self.disconnect()
    
    def duplicate_user(self,id):
        try:
            self.connect()
            sql = f"SELECT * FROM users where id = %s"
            value = (id,)
            self.cursor.execute(sql,value)
            result = self.cursor.fetchone()
            if result:
                return True
            else:
                return False
        except mysql.connector.Error as error:
            print(f"게시글 조회 실패: {error}")
            return []
        finally:
            self.disconnect()
    
    def get_user_by_id(self,id):
        try:
            self.connect()
            sql = f"SELECT * FROM users WHERE id = %s"
            value = (id,) # 튜플에 값이 한개만 들어갈때 ,해줘야됨 
            self.cursor.execute(sql, value)
            return self.cursor.fetchone()
        except mysql.connector.Error as error:
            print(f"데이터베이스 연결 실패: {error}")
            return None
        finally:
            self.disconnect()       
            
    def delete_user(self, id):
        try:
            self.connect()
            sql = f"DELETE FROM users WHERE id = %s"
            value = (id,) # 튜플에 값이 한개만 들어갈때 ,해줘야됨 
            self.cursor.execute(sql, value)
            self.connection.commit()
            flash("회원 탈퇴 성공!",'success')
            return True
        except mysql.connector.Error as error:
            print(f"유저 삭제 실패: {error}")
            return False
        finally:
            self.disconnect()
            
    def get_user_edit_password(self, id, password):
        try:
            self.connect()
            sql = f"UPDATE users SET `password` = PASSWORD(%s) WHERE `id`=%s"
            value = (password,id) # 튜플에 값이 한개만 들어갈때 ,해줘야됨 
            self.cursor.execute(sql, value)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            print(f"게시글 조회수 증가 실패: {error}")
            return False
        finally:
            self.disconnect()    
    
    def moives_images(self):
        """
        주어진 URL에서 이미지를 다운로드하여 save_dir에 저장
        :param url: 이미지가 포함된 웹 페이지 URL
        :param save_dir: 이미지를 저장할 로컬 디렉토리 경로
        """
        url = "https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&ssc=tab.nx.all&query=%EC%98%81%ED%99%94+%EC%88%9C%EC%9C%84&oquery=%EC%98%81%ED%99%94&tqi=iGpiYdqVOsossurWSGlssssssC4-514797"  # 이미지를 포함한 웹 페이지 URL
        save_dir = "static/images"  
        # 요청 및 파싱
        response = requests.get(url)
        response.raise_for_status()  # 요청 에러 확인
        soup = BeautifulSoup(response.text, 'html.parser')

        items = soup.select('div.list_image_info.type_pure_top div ul:nth-child(1) li')
        # 이미지 태그 추출
        img_tags = soup.find_all('img')[:10]
        title =[]
        for item in items[:10]:
            title.append(item.select_one('strong').text)


        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    

        # 이미지 다운로드
        for idx, img_tag in enumerate(img_tags):
            img_url = img_tag.get('src')

            if not img_url:
                continue  # src 속성이 없는 경우 건너뛰기

            # 절대 URL인지 확인하고 없으면 상대 URL 처리
            if not img_url.startswith(('http://', 'https://')):
                img_url = requests.compat.urljoin(url, img_url)

            print(f"Downloading {img_url}...")

            try:
                img_response = requests.get(img_url)
                img_response.raise_for_status()

                # 파일 저장
                img_name = f"{title[idx]}.jpg"
                img_path = os.path.join(save_dir, img_name)
                with open(img_path, 'wb') as file:
                    file.write(img_response.content)

                print(f"Saved: {img_path}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {img_url}: {e}")

    # def movies_merge(self):
    #     try:
    #         matched_data = []
    #         self.connect()
    #         self.cursor.execute("SELECT title FROM movies_info")
    #         movies_info = self.cursor.fetchall()
    #         print(movies_info)
    #         image_files = os.listdir("static/images")
    #         for movie_info in movies_info:
    #             title = movie_info['title']
    #             for image_file in image_files:
    #                 image_name, _ = os.path.splitext(image_file)
    #                 if title == image_name:
    #                     matched_data.append({
    #                         'title' : title,
    #                         'filename' : image_file
    #                     })
    #                 else:
    #                     matched_data.append({
    #                         'title' : title,
    #                         'filename' : "noimage.jpg"
    #                     })                        
    #         return metched_data
    #     except mysql.connector.Error as error:
    #         print(f"image파일과 데이터 베이스 연결 실패: {error}")
    #     finally:
    #         self.disconnect()
    
    def update_filename_in_db(self, table_name):
        """
        title 컬럼을 기준으로 filename 컬럼 업데이트
        :param image_dir: 이미지 파일이 저장된 디렉토리 경로
        :param table_name: 업데이트할 테이블 이름
        """
        try:
            self.connect()

            # 이미지 파일 목록 가져오기
            image_files = os.listdir('static/images')

            # SQL로 title 데이터 가져오기
            self.cursor.execute(f"SELECT id, title FROM {table_name}")
            rows = self.cursor.fetchall()

            for row in rows:
                title = row['title']
                # 이미지 파일 이름 매칭
                matched_file = None
                for image_file in image_files:
                    file_name, _ = os.path.splitext(image_file)
                    if title == file_name:
                        matched_file = image_file
                        break

                # 이미지가 없으면 noimage.jpg 저장
                if not matched_file:
                    matched_file = "noimage.jpg"

                # SQL UPDATE
                sql = f"""
                    UPDATE {table_name}
                    SET filename = %s
                    WHERE title = %s;
                """
                values = (matched_file, title)
                self.cursor.execute(sql, values)

            # 변경 사항 저장
            self.connection.commit()
            print(f"{self.cursor.rowcount} rows updated in {table_name} table.")

        except mysql.connector.Error as error:
            print(f"Error updating filename: {error}")
        finally:
                self.disconnect()
                
    def moives_info(self):
        servicekey = 'd8df4fae219ac24585a0ee3c1a43933c'
        # 오늘 날짜를 '250113' 형식으로 가져오기
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        yesterday_formatted = yesterday.strftime('%Y%m%d')

        url = f'http://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json?key={servicekey}&targetDt={yesterday_formatted}'
        res = requests.get(url)
        today_datas = res.json()

        t_datas = []
        for data in today_datas["boxOfficeResult"]["dailyBoxOfficeList"]:
            movie_data ={
                "rank": data["rank"],
                "title": data["movieNm"],
                "release_date": data["openDt"],
                "t_sales": data["salesAmt"],
                "c_sales": data["salesAcc"],
                "t_audience": data["audiCnt"],
                "c_audience": data["audiAcc"],
                "moviecd": data['movieCd']
            }
            t_datas.append(movie_data)

        m_infos = []
        for data in t_datas:
            url1 = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?key={servicekey}&movieCd={data['moviecd']}'
            res1 = requests.get(url1)
            movie_infos = res1.json()

            # movieCd 가져오기
            movie_cd = movie_infos["movieInfoResult"]["movieInfo"]["movieCd"]
            # nationNm 가져오기
            nations = [nation["nationNm"] for nation in movie_infos["movieInfoResult"]["movieInfo"]["nations"]][0]
            # genreNm 가져오기
            genres = [genre["genreNm"] for genre in movie_infos["movieInfoResult"]["movieInfo"]["genres"]][0]
            # peopleNm 가져오기 (actors 리스트에서)
            director = [director["peopleNm"] for director in movie_infos["movieInfoResult"]["movieInfo"]["directors"]][0]
            # 결과를 딕셔너리 형태로 저장
            result = {
                "moviecd": movie_cd,
                "nations": nations,
                "genres": genres,
                "director": director
            }
            m_infos.append(result)

        df1 = pd.DataFrame(t_datas)
        df2 = pd.DataFrame(m_infos)
        df3 = pd.merge(df1, df2, on='moviecd', how='inner')
        df3 = df3[['rank','title','genres','director','nations','t_audience','c_audience','t_sales','c_sales','release_date','moviecd']]
        # df3 = df3['순위']
        df3['rank']=df3['rank'].astype(int)
        df3['t_audience']=df3['t_audience'].astype(int)
        df3['c_audience']=df3['c_audience'].astype(int)
        df3['t_sales']=df3['t_sales'].astype(int)
        df3['c_sales']=df3['c_sales'].astype(int)
        print("영화 정보 가져오기 완료!") 
        self.insert_data(df3)
        self.insert_data_with_no_duplicates(df3)
   
    def clear_table(self):
        """
        테이블의 모든 데이터를 삭제
        """
        try:
            self.connect()
            sql = "TRUNCATE TABLE movies_info;"
            self.cursor.execute(sql)
            self.connection.commit()
            print("Table movies_info cleared.")
        except mysql.connector.Error as error:
            print(f"movies_info 테이블 데이터 삭제 실패: {error}")
        finally:
            self.disconnect()

    def check_title_exists(self, title):
        """
        제목 중복 확인 함수
        """
        try:
            self.connect()
            # dictionary=False로 일반 커서 생성
            self.cursor = self.connection.cursor(dictionary=False)
            
            sql = "SELECT COUNT(*) FROM movies WHERE title = %s"
            self.cursor.execute(sql, (title,))
            count = self.cursor.fetchone()[0]
            return count > 0
            
        except mysql.connector.Error as error:
            print(f"Error checking title existence: {error}")
            return False
        finally:
            self.disconnect()

    def insert_data_with_no_duplicates(self, df):
        """
        제목이 중복되지 않는 경우에만 데이터프레임의 데이터를 한 번에 삽입
        """
        connection = None
        cursor = None
        
        try:
            # 새로운 연결 생성
            connection = mysql.connector.connect(
                host='10.0.66.20',
                user='sejong',
                password='1234',
                database='movie_db',
                connection_timeout=600
            )
            cursor = connection.cursor(dictionary=False)
            
            # 중복이 없는 데이터를 저장할 리스트
            data_to_insert = []

            for _, row in df.iterrows():
                print(f"Processing row: {row['title']}")
                
                # 중복 확인을 위한 쿼리
                check_sql = "SELECT COUNT(*) FROM movies WHERE title = %s"
                cursor.execute(check_sql, (row['title'],))
                if cursor.fetchone()[0] == 0:  # 중복이 없는 경우
                    try:
                        values = (
                            int(row['rank']),
                            str(row['title']),
                            str(row['genres']),
                            str(row['director']),
                            str(row['nations']),
                            int(row['t_audience']),
                            int(row['c_audience']),
                            int(row['t_sales']),
                            int(row['c_sales']),
                            row['release_date']
                        )
                        data_to_insert.append(values)
                        print(f"Added to insert list: {row['title']}")
                    except ValueError as e:
                        print(f"Data conversion error for {row['title']}: {e}")
                else:
                    print(f"Skipped duplicate: {row['title']}")

            # 데이터가 있을 경우만 삽입
            if data_to_insert:
                sql = """
                    INSERT INTO movies 
                    (rank, title, genres, director, nations, t_audience, c_audience, t_sales, c_sales, release_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.executemany(sql, data_to_insert)
                connection.commit()
                print(f"Successfully inserted {len(data_to_insert)} records.")
                
                for record in data_to_insert:
                    print(f"Inserted: {record[1]}")
            else:
                print("No new data to insert.")

        except mysql.connector.Error as error:
            print(f"Database error: {error}")
            if connection and connection.is_connected():
                connection.rollback()
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
                print("Database connection closed.")



    def insert_data(self, df):
        """
        movies_info 테이블에 데이터를 삽입
        """
        try:
            self.clear_table()
            self.connect()
            for _, row in df.iterrows():
                sql = """
                    INSERT INTO movies_info (rank, title, genres, director, nations, t_audience, c_audience, t_sales, c_sales, release_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (row['rank'], row['title'], row['genres'], row['director'], row['nations'], row['t_audience'], row['c_audience'], row['t_sales'], row['c_sales'], row['release_date'])
                self.cursor.execute(sql, values)
            self.connection.commit()
            print("movies_info 테이블 업데이트 완료.")
        except mysql.connector.Error as error:
            print(f"movies_info 테이블 데이터 삽입 실패: {error}")
        finally:
            self.disconnect()


    def get_all_movies(self):
        try:
            self.connect()
            sql = f"SELECT * FROM movies_info"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except mysql.connector.Error as error:
            print(f"영화데이터 조회 실패: {error}")
            return []
        finally:
            self.disconnect()