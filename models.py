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
import re



class DBManager:
    def __init__(self):
        # MySQL 데이터베이스 연결
        self.connection = None
        self.cursor = None
        
    def connect(self):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host='192.168.0.19',
                    user='junhyuk',
                    password='1234',
                    database='movie_db',
                    connection_timeout=600  # 10분
                )
                self.cursor = self.connection.cursor(dictionary=True)
        except mysql.connector.Error as error:
            print(f"데이터베이스 연결 실패: {error}")
            
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
#--------------------------기본값으로 설정--------------------------------★    
        
    ### 회원가입
    def regsiter_user(self, name, id, password,user_ip, filename):
        try:
            self.connect()
            sql = f"INSERT INTO users (name, user_id, password, user_ip,filename) values (%s, %s, password(%s),%s, %s)"
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
    
    ### 로그인
    def login_user(self, id, password):
        try:
            self.connect()
            sql = f"SELECT * FROM users where user_id = %s and password=password(%s) and deleted_at IS NULL"
            values = (id, password)
            self.cursor.execute(sql,values)
            return self.cursor.fetchone()
        except mysql.connector.Error as error:
            flash("계정 조회 실패", "error")
            print(f"계정 조회 실패: {error}")
            return []
        finally:
            self.disconnect()
    
    ### 회원가입시 id 중복 확인
    def duplicate_user(self,id):
        try:
            self.connect()
            sql = f"SELECT * FROM users where user_id = %s and deleted_at IS NULL"
            value = (id,)
            self.cursor.execute(sql,value)
            result = self.cursor.fetchone()
            if result:
                return True
            else:
                sql = "SELECT * FROM "
                return False
        except mysql.connector.Error as error:
            print(f"게시글 조회 실패: {error}")
            return []
        finally:
            self.disconnect()
    
    ### 해당 id 유저정보 가져오기
    def get_user_by_id(self,id):
        try:
            self.connect()
            sql = f"SELECT * FROM users WHERE user_id = %s and deleted_at IS NULL"
            value = (id,) # 튜플에 값이 한개만 들어갈때 ,해줘야됨 
            self.cursor.execute(sql, value)
            return self.cursor.fetchone()
        except mysql.connector.Error as error:
            print(f"데이터베이스 연결 실패: {error}")
            return None
        finally:
            self.disconnect()     

    ### 해당 id 유저 비밀번호 변경
    def get_user_edit_password(self, id, password):
        try:
            self.connect()
            sql = f"UPDATE users SET `password` = PASSWORD(%s) WHERE `user_id`=%s and deleted_at IS NULL"
            value = (password,id) # 튜플에 값이 한개만 들어갈때 ,해줘야됨 
            self.cursor.execute(sql, value)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            print(f"게시글 조회수 증가 실패: {error}")
            return False
        finally:
            self.disconnect()   

    ### 해당 id 유저 회원 탈퇴
    def delete_user(self, id):
        try:
            self.connect()
            sql = f"UPDATE users SET deleted_at = NOW() WHERE user_id = %s;"
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

    ### 모든 리뷰 정보 가져오기
    def get_all_posts(self):
        try:
            self.connect()
            sql = f"SELECT * FROM posts where deleted_at IS NULL"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except mysql.connector.Error as error:
            print(f"게시글 조회 실패: {error}")
            return []
        finally:
            self.disconnect()
        
    ### 리뷰 추가하기    
    def insert_post(self, title, content, filename, userid, username, rating, spoiler, movie_title, movie_id):
        try:
            self.connect()

            # 1️⃣ 게시글 추가
            sql = """
                INSERT INTO posts (title, content, filename, created_at, userid, username, rating, spoiler, movie_title, movie_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (title, content, filename, datetime.now(), userid, username, rating, spoiler, movie_title, movie_id)
            self.cursor.execute(sql, values)

            # 2️⃣ users 테이블 업데이트 (posts +1, popcorns +5)
            self.cursor.execute("""
                UPDATE users 
                SET posts = IFNULL(posts, 0) + 1, 
                    popcorns = IFNULL(popcorns, 0) + 5 
                WHERE user_id = %s
            """, (userid,))

            self.connection.commit()  # ✅ 트랜잭션 커밋
            return True

        except mysql.connector.Error as error:
            print(f"게시글 추가 실패: {error}")
            if self.connection:
                self.connection.rollback()  # ❌ 오류 발생 시 롤백
            return False

        finally:
            self.disconnect()
       
    ### 선택된 리뷰 자세히 보기     
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
            
    ### 리뷰 수정
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
    
    ### 리뷰 삭제
    def delete_post(self, post_id, user_id):
        try:
            self.connect()

            # 1️⃣ 리뷰 삭제 (deleted_at 업데이트)
            sql = "UPDATE posts SET deleted_at = NOW() WHERE id = %s;"
            value = (post_id,)
            self.cursor.execute(sql, value)

            # 2️⃣ users 테이블 업데이트 (posts -1, popcorns -5, popcorns는 최소 0 이상)
            self.cursor.execute("""
                UPDATE users 
                SET posts = GREATEST(IFNULL(posts, 0) - 1, 0), 
                    popcorns = GREATEST(IFNULL(popcorns, 0) - 5, 0) 
                WHERE user_id = %s
            """, (user_id,))

            self.connection.commit()  # ✅ 트랜잭션 커밋
            print("✅ 리뷰 삭제 및 users 테이블 업데이트 완료.")
            return True

        except mysql.connector.Error as error:
            print(f"❌ 리뷰 삭제 실패: {error}")
            if self.connection:
                self.connection.rollback()  # ❌ 오류 발생 시 롤백
            return False

        finally:
            self.disconnect()
    
    ### 리뷰 조회수     
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

    ### 리뷰 추천수        
    def recommend_post(self, id):
        try:
            # 데이터베이스 연결
            self.connect()

            # 추천 수 증가
            sql = f"UPDATE posts SET recommend = recommend + 1 WHERE id = %s"
            value = (id,)
            self.cursor.execute(sql, value)
            self.connection.commit()

            # 추천 완료 메시지
            flash('추천이 성공적으로 처리되었습니다!', 'success')

        except Exception as e:
            # 오류 처리
            print(f"Error: {e}")
            flash('추천 처리 중 오류가 발생했습니다.', 'danger')
        finally:
            self.disconnect()   
    
    ### 리뷰 신고수
    def report_post_count(self, id):
        try:
            # 데이터베이스 연결
            self.connect()

            # 신고수 증가
            sql = f"UPDATE posts SET report = report + 1 WHERE id = %s"
            value = (id,)
            self.cursor.execute(sql, value)
            self.connection.commit()

            # 신고고 완료 메시지
            flash('신고가 성공적으로 처리되었습니다!', 'success')

        except Exception as e:
            # 오류 처리
            print(f"Error: {e}")
            flash('신고 처리 중 오류가 발생했습니다.', 'danger')
        finally:
            self.disconnect()   
    
    
    ### 신고 내용 저장
    def report_post(self, post_id,reporter_id, content, reason_code,movie_title,writer_id):
        try:
            # 데이터베이스 연결
            self.connect()

            # 신고 내용 저장
            sql = f"INSERT INTO reports (post_id,reporter_id,movie_title,writer_id, content, reason_code) VALUES (%s, %s, %s, %s, %s, %s)"
            value = (post_id,reporter_id, movie_title,writer_id, content, reason_code)
            self.cursor.execute(sql, value)
            self.connection.commit()

            flash('신고가 성공적으로 접수되었습니다.', 'success')
        except Exception as e:
            print(f"Error: {e}")
            flash('신고 처리 중 문제가 발생했습니다.', 'danger')
        finally:
            self.disconnect()


    ### 영화 이미지 requests, BeautifulSoup을 활용하여 제목과 함께 저장    
    def movies_images(self):
        url = "https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&ssc=tab.nx.all&query=%EC%98%81%ED%99%94+%EC%88%9C%EC%9C%84"
        base_dir = os.path.abspath(os.getcwd())
        save_dir = os.path.join(base_dir, "static", "images")

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 먼저 전체 제목 리스트를 가져옴 (Processing row에서 사용하는 방식과 동일)
        items = soup.select('div.list_image_info.type_pure_top div ul:nth-child(1) li')
        titles = []
        for item in items[:10]:
            # Processing row에서 사용하는 것과 동일한 방식으로 제목 추출
            title = item.select_one('strong').text.strip()
            titles.append(title)

        # 이미지 태그 찾기
        img_tags = soup.find_all('img')[:10]

        # 제목과 이미지를 함께 처리
        for idx, (title, img_tag) in enumerate(zip(titles, img_tags)):
            try:
                img_url = img_tag.get('src')
                if not img_url:
                    print(f"No image URL found for {title}")
                    continue

                img_url = requests.compat.urljoin(url, img_url)
                print(f"Downloading {img_url}...")

                img_response = requests.get(img_url)
                img_response.raise_for_status()

                # 파일 이름 생성
                sanitized_title = self.sanitize_filename(title)
                img_name = f"{sanitized_title}.jpg"
                img_path = os.path.join(save_dir, img_name)

                # 디버깅 로그
                print(f"Original title: {title}")
                print(f"Sanitized title: {sanitized_title}")
                print(f"Image name: {img_name}")
                print(f"Image path: {img_path}")

                with open(img_path, 'wb') as file:
                    file.write(img_response.content)
                print(f"Saved: {img_path}")

            except Exception as e:
                print(f"Error processing movie: {e}")
                import traceback
                print(traceback.format_exc())

    ### 파일 이름 유효성 체크
    def sanitize_filename(self, filename):
        # Windows에서 사용할 수 없는 문자 처리
        invalid_chars = '<>:"/\\|?*'
        # filename = filename.replace(':', '_')  # 콜론을 언더스코어로 변경
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()  # 앞뒤 공백 제거

    ### 이미지파일 movies 테이블에 업데이트
    def update_filename_in_db(self, table_name):
        """
        데이터베이스에서 title 컬럼에 해당하는 filename 값을 업데이트합니다.
        """
        try:
            self.connect()

            # 이미지 파일 목록 가져오기
            image_files = os.listdir("static/images")
            noimage_path = os.path.join('static/images', 'noimage.jpg')

            # noimage.jpg 확인
            if 'noimage.jpg' not in image_files:
                print("Warning: 'noimage.jpg' 파일이 존재하지 않습니다.")

            # SQL로 title 데이터 가져오기
            self.cursor.execute(f"SELECT id, title FROM {table_name}")
            rows = self.cursor.fetchall()

            for row in rows:
                title = row['title']
                sanitized_title = self.sanitize_filename(title)
                matched_file = None

                # 이미지 파일 이름 매칭
                for image_file in image_files:
                    file_name, _ = os.path.splitext(image_file)
                    if sanitized_title[:15] == file_name[:15]:
                        matched_file = image_file
                        break

                # 이미지가 없으면 noimage.jpg 사용
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

    ### KOBIS사이트에서 일별 박스오피스 및 영화 상세정보 API 가져와서 PANDAS를 활용하여 필요한 데이터 추출    
    def moives_info(self):
        servicekey = '53fa9a76096ef93b1c1b820726b47755'
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        yesterday_formatted = yesterday.strftime('%Y%m%d')

        url = f'http://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json?key={servicekey}&targetDt={yesterday_formatted}'
        res = requests.get(url)
        today_datas = res.json()

        t_datas = []
        for data in today_datas["boxOfficeResult"]["dailyBoxOfficeList"]:
            movie_data = {
                "rank": data["rank"],
                "title": data["movieNm"],
                "release_date": data["openDt"],
                "t_sales": data["salesAmt"],
                "c_sales": data["salesAcc"],
                "t_audience": data["audiCnt"],
                "c_audience": data["audiAcc"],
                "moviecd": data["movieCd"]
            }
            t_datas.append(movie_data)

        m_infos = []
        for data in t_datas:
            url1 = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?key={servicekey}&movieCd={data["moviecd"]}'
            res1 = requests.get(url1)
            movie_infos = res1.json()

            # ✅ API 응답 확인
            print(f"🎬 {data['title']} ({data['moviecd']}) API 응답:", movie_infos)

            # ✅ KeyError 방지
            if "movieInfoResult" not in movie_infos or "movieInfo" not in movie_infos["movieInfoResult"]:
                print(f"❌ 'movieInfoResult' 또는 'movieInfo' 키 없음! (movieCd: {data['moviecd']})")
                continue

            movie_data = movie_infos["movieInfoResult"]["movieInfo"]

            nations = movie_data.get("nations", [])
            nations = nations[0]["nationNm"] if nations else "Unknown"

            genres = movie_data.get("genres", [])
            genres = genres[0]["genreNm"] if genres else "Unknown"

            # ✅ `directors` 리스트가 비어 있을 경우 기본 값 "Unknown" 반환
            directors = movie_data.get("directors", [])
            director = directors[0]["peopleNm"] if directors else "Unknown"

            result = {
                "moviecd": data["moviecd"],
                "nations": nations,
                "genres": genres,
                "director": director
            }
            m_infos.append(result)

        df1 = pd.DataFrame(t_datas)
        df2 = pd.DataFrame(m_infos)
        df3 = pd.merge(df1, df2, on='moviecd', how='inner')

        df3['c_sales'] = df3['c_sales'].fillna(0).astype('int64')
        df3['rank'] = df3['rank'].astype(int)
        df3['t_audience'] = df3['t_audience'].astype(int)
        df3['c_audience'] = df3['c_audience'].astype(int)
        df3['t_sales'] = df3['t_sales'].astype(int)

        print("🎬 영화 정보 가져오기 완료!")
        self.insert_data_with_no_duplicates(df3)
        print(df3)

    def insert_data_with_no_duplicates(self, df):
        try:
            self.connect()
            for _, row in df.iterrows():
                print(f"Processing row: {row['title']} ({row['director']})")
                
                # 중복 확인 쿼리 (title + director 조합 확인)
                check_sql = "SELECT * FROM movies WHERE BINARY TRIM(title) = BINARY TRIM(%s) AND BINARY TRIM(director) = BINARY TRIM(%s)"
                self.cursor.execute(check_sql, (row['title'].strip(), row['director'].strip()))
                existing_record = self.cursor.fetchone()

                print(f"🔍 DEBUG: Existing Record for {row['title']} ({row['director']}): {existing_record}")

                
                if existing_record:
                    record_exists = True
                else:
                    record_exists = False
                
                values = (
                    int(row['rank']),
                    str(row['genres']).strip(),
                    str(row['nations']).strip(),
                    int(row['t_audience']),
                    int(row['c_audience']),
                    int(row['t_sales']),
                    int(row['c_sales']),
                    row['release_date'],
                    datetime.now() + timedelta(hours=9)  # 현재 시간 추가
                )
                
                if record_exists:
                    print(f"Updating: {row['title']} ({row['director']})")
                    update_sql = """
                        UPDATE movies
                        SET rank = COALESCE(%s, rank), genres = COALESCE(%s, genres), nations = COALESCE(%s, nations),
                            t_audience = COALESCE(%s, t_audience), c_audience = COALESCE(%s, c_audience), t_sales = COALESCE(%s, t_sales),
                            c_sales = COALESCE(%s, c_sales), release_date = COALESCE(%s, release_date),
                            input_date = %s
                        WHERE BINARY TRIM(title) = BINARY TRIM(%s) AND BINARY TRIM(director) = BINARY TRIM(%s)
                    """
                    update_values = values + (row['title'].strip(), row['director'].strip())
                    print(f"🔹 Update Values: {update_values}")
                    self.cursor.execute(update_sql, update_values)
                    self.connection.commit()
                    
                    if self.cursor.rowcount == 0:
                        print(f"⚠ Warning: No rows were updated for {row['title']} ({row['director']})")
                        
                        # 업데이트 실패 시 데이터 조회하여 확인
                        self.cursor.execute("SELECT * FROM movies WHERE BINARY TRIM(title) = BINARY TRIM(%s) AND BINARY TRIM(director) = BINARY TRIM(%s)",
                                           (row['title'].strip(), row['director'].strip()))
                        existing_record = self.cursor.fetchone()
                        print(f"🔍 DB 상태 확인 (업데이트 후): {existing_record}")
                else:
                    print(f"📌 Attempting to INSERT: {row['title']} ({row['director']})")
                    insert_sql = """
                        INSERT INTO movies 
                        (rank, genres, nations, t_audience, c_audience, t_sales, c_sales, release_date, title, director, input_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    insert_values = values + (row['title'].strip(), row['director'].strip())
                    print(f"🎯 Insert Values: {insert_values}")
                    self.cursor.execute(insert_sql, insert_values)
                    self.connection.commit()
                    print(f"✅ Inserted: {row['title']} ({row['director']})")
                
            print("Database update completed successfully.")
        
        except mysql.connector.Error as error:
            print(f"Database error: {error}")
            if self.connection and self.connection.is_connected():
                self.connection.rollback()
        finally:
            self.disconnect()

    ### 오늘 날짜의 영화 정보 가져오기
    def get_all_movies(self):
        try:
            self.connect()
            today_date = datetime.today().strftime('%Y-%m-%d')
            sql = "SELECT * FROM movies WHERE DATE(input_date) = %s order by rank asc"
            self.cursor.execute(sql, (today_date,))
            return self.cursor.fetchall()
        except mysql.connector.Error as error:
            print(f"영화 데이터 조회 실패: {error}")
            return []
        finally:
            self.disconnect()

    def get_all_popcorns_movies(self):
        """모든 영화 정보를 popcorns가 많은 순으로 가져오기"""
        try:
            self.connect()
            query = """
                SELECT m.id, m.title, m.director, m.rating, m.reviews, m.filename, m.c_audience, 
                    COALESCE(l.popcorns, 0) AS popcorns
                FROM movies m
                LEFT JOIN (
                    SELECT movie_id, SUM(popcorns) AS popcorns 
                    FROM lots 
                    GROUP BY movie_id
                ) l ON m.id = l.movie_id
                ORDER BY popcorns DESC
            """
            self.cursor.execute(query)
            movies = self.cursor.fetchall()
            return movies
        except mysql.connector.Error as error:
            print(f"영화 데이터 조회 실패: {error}")
            return []
        finally:
            self.disconnect()

    ### 댓글 추가
    def insert_comment(self, post_id, user_id, user_name, content):
        try:
            self.connect()

            # 1️⃣ 댓글 추가
            sql = """
                INSERT INTO comments (post_id, user_id, user_name, content, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (post_id, user_id, user_name, content, datetime.now())
            self.cursor.execute(sql, values)

            # 2️⃣ users 테이블 업데이트 (comments +1, popcorns +3)
            self.cursor.execute("""
                UPDATE users 
                SET comments = IFNULL(comments, 0) + 1, 
                    popcorns = IFNULL(popcorns, 0) + 2 
                WHERE user_id = %s
            """, (user_id,))

            self.connection.commit()  # ✅ 트랜잭션 커밋
            print("✅ 댓글 추가 및 users 테이블 업데이트 완료.")
            return True

        except mysql.connector.Error as error:
            print(f"❌ 댓글 추가 실패: {error}")
            if self.connection:
                self.connection.rollback()  # ❌ 오류 발생 시 롤백
            return False

        finally:
            self.disconnect()

    ### 모든 댓글 정보 가져오기
    def get_all_comments(self):
        try:
            self.connect()
            sql = f"SELECT * FROM comments where deleted_at IS NULL"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except mysql.connector.Error as error:
            print(f"댓글 조회 실패: {error}")
            return []
        finally:
            self.disconnect()
            
    ### 해당 id 데이터 가져오기
    def get_comment_by_id(self, id):
        try:
            self.connect()
            sql = f"SELECT * FROM comments WHERE id = %s and deleted_at IS NULL"
            value = (id,) # 튜플에 값이 한개만 들어갈때 ,해줘야됨 
            self.cursor.execute(sql, value)
            return self.cursor.fetchone()
        except mysql.connector.Error as error:
            print(f"데이터베이스 연결 실패: {error}")
            return None
        finally:
            self.disconnect()
        
    def delete_comment(self, comment_id, user_id):
        try:
            self.connect()

            print(f"🔍 [DEBUG] delete_comment() 실행 - 댓글 ID: {comment_id}, 사용자 ID: {user_id}")

            # 댓글 삭제 SQL 실행
            sql = "UPDATE comments SET deleted_at = NOW() WHERE id = %s AND deleted_at IS NULL;"
            value = (comment_id,)
            self.cursor.execute(sql, value)

            print(f"🔍 [DEBUG] 실행된 rowcount: {self.cursor.rowcount}")  # ✅ rowcount 확인

            # ✅ rowcount가 0이면 삭제되지 않은 것 → 원인 분석 필요
            if self.cursor.rowcount == 0:
                print(f"⚠ Warning: 댓글 ID {comment_id} 삭제 실패 (이미 삭제되었거나 존재하지 않음)")
                return False

            # 2️⃣ users 테이블 업데이트 (comments -1, popcorns -3, popcorns는 최소 0 이상)
            self.cursor.execute("""
                UPDATE users 
                SET comments = GREATEST(IFNULL(comments, 0) - 1, 0), 
                    popcorns = GREATEST(IFNULL(popcorns, 0) - 3, 0) 
                WHERE user_id = %s
            """, (user_id,))

            self.connection.commit()  # ✅ 트랜잭션 커밋
            print(f"✅ 댓글 삭제 완료: ID {comment_id}, 사용자 {user_id}")
            return True

        except mysql.connector.Error as error:
            print(f"❌ 댓글 삭제 실패: {error}")
            if self.connection:
                self.connection.rollback()  # ❌ 오류 발생 시 롤백
            return False

        finally:
            self.disconnect()


            
    def comment_post_count(self, id):
        try:
            # 데이터베이스 연결
            self.connect()
            # 댓글수 증가
            sql = f"UPDATE posts SET comment = comment + 1 WHERE id = %s"
            value = (id,)
            self.cursor.execute(sql, value)
            self.connection.commit()

        except Exception as e:
            # 오류 처리
            print(f"Error: {e}")
            flash('댓글 처리 중 오류가 발생했습니다.', 'danger')
        finally:
            self.disconnect()   

    def movies_reviews_count(self, title):
        try:
            # 데이터베이스 연결
            self.connect()
            # 댓글수 증가
            sql = f"UPDATE movies SET reviews = reviews + 1 WHERE title = %s"
            value = (title,)
            self.cursor.execute(sql, value)
            self.connection.commit()

        except Exception as e:
            # 오류 처리
            print(f"Error: {e}")
            flash('리뷰 카운터 처리 중 오류가 발생했습니다.', 'danger')
        finally:
            self.disconnect()   


    def update_movie_ratings_and_reviews(self):
        try:
            # 데이터베이스 연결
            self.connect()

            # 영화 제목별 평균 rating 및 리뷰 개수 계산
            self.cursor.execute("""
                SELECT 
                    movie_title,
                    AVG(rating) AS avg_rating,
                    COUNT(*) AS review_count
                FROM 
                    posts
                WHERE 
                    rating IS NOT NULL
                GROUP BY 
                    movie_title
            """)
            aggregated_data = self.cursor.fetchall()

            # movies 테이블 업데이트
            for row in aggregated_data:
                movie_title = row['movie_title']
                avg_rating = row['avg_rating']
                review_count = row['review_count']

                # 영화 제목에 해당하는 평균 rating 및 리뷰 개수 업데이트
                self.cursor.execute("""
                    UPDATE movies
                    SET rating = %s, reviews = %s
                    WHERE title = %s
                """, (avg_rating, review_count, movie_title))

            # 변경사항 커밋
            self.connection.commit()
            print("Movies table updated successfully!")

        except mysql.connector.Error as error:
            print(f"Error updating movie ratings and reviews: {error}")
        finally:
            self.disconnect()

    
    def view_reports(self):
        try:
            self.connect()

            # reports 테이블에서 데이터 가져오기
            self.cursor.execute("SELECT * FROM reports")
            return self.cursor.fetchall()

        except mysql.connector.Error as error:
            print(f"Error fetching reports: {error}")
            return "Error loading reports."

        finally:
            self.disconnect()

    def loc_ip(self, user_ip):
        url = f"https://ipinfo.io/{user_ip}?token=08f027512e9236"
        try:
            response = requests.get(url)
            data = response.json()  # JSON 응답을 딕셔너리로 변환
            
            if "loc" in data:
                return data["loc"]  # 위도, 경도 반환
            else:
                return "Location not found"

        except requests.exceptions.RequestException as e:
            return f"Error: {e}"

    def popcorns_lot(self, movie_id, movie_title, user_id):
        """추첨 기능 (lots +1, popcorns -10)"""
        try:
            self.connect()

            # 🔍 사용자의 현재 popcorns 조회
            self.cursor.execute("SELECT popcorns FROM users WHERE user_id = %s", (user_id,))
            user = self.cursor.fetchone()

            if user is None:
                return "사용자를 찾을 수 없습니다!"
            
            user_popcorns = user["popcorns"] if user["popcorns"] is not None else 0

            if user_popcorns < 10:
                return "팝콘이 부족합니다!"  # 🚨 팝콘 부족 오류 반환

            # 🔍 lots 테이블 확인 (기존 데이터 있는지 체크)
            self.cursor.execute("SELECT popcorns FROM lots WHERE movie_id = %s AND user_id = %s", (movie_id, user_id))
            existing_lot = self.cursor.fetchone()

            if existing_lot:
                # 기존 항목이 있으면 popcorns 증가
                new_popcorns = existing_lot["popcorns"] + 10
                self.cursor.execute("UPDATE lots SET popcorns = %s WHERE movie_id = %s AND user_id = %s",
                                    (new_popcorns, movie_id, user_id))
            else:
                # 없으면 새로 추가
                self.cursor.execute("INSERT INTO lots (movie_id, movie_title, user_id, popcorns) VALUES (%s, %s, %s, 10)",
                                    (movie_id, movie_title, user_id))

            # 🔹 users 테이블 업데이트 (lots +1, popcorns -10)
            self.cursor.execute("UPDATE users SET lots = IFNULL(lots, 0) + 1, popcorns = popcorns - 10 WHERE user_id = %s", (user_id,))

            self.connection.commit()
            return True  # ✅ 성공

        except mysql.connector.Error as error:
            print(f"Database error: {error}")
            if self.connection:
                self.connection.rollback()
            return "데이터 처리 중 오류 발생!"

        finally:
            self.disconnect()

            