from flask import Flask, url_for, render_template, send_from_directory, jsonify ,request, redirect, session,flash
from functools import wraps
import os
from datetime import datetime
from models import DBManager
import pandas as pd


app = Flask(__name__)
app.secret_key = 'your-secret-key'
# app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static','uploads')
app.config['USER_IMAGE_FOLDER'] = os.path.join(app.root_path, 'static','user_image')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


manager = DBManager()
manager.moives_info()
manager.movies_images()
manager.update_filename_in_db("movies_info")
manager.update_filename_in_db("movies")


### images 폴더 static/images 폴더로 연결
@app.route('/images/<path:filename>')
def img_file(filename):
    return send_from_directory('static/images', filename)

### js 폴더 static/js 폴더로 연결
@app.route('/js/<path:filename>')
def js_file(filename):
    return send_from_directory('static/js', filename)

### user_image 폴더 static/user_image 폴더로 연결
@app.route('/user_image/<path:filename>')
def user_img_file(filename):
    return send_from_directory('static/user_image', filename)

### uploads 폴더 static/uploads폴더로 연결
@app.route('/uploads/<path:filename>')
def uploads_file(filename):
    return send_from_directory('static/uploads', filename)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

### 로그인
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':
        id = request.form.get('userid')
        password = request.form.get('password')
        user = manager.login_user(id, password)
        if user:
            session['id'] = id
            session['name'] = user['name']
            session['filename'] = user['filename']
            
            return f'<script>alert("로그인 성공!");location.href="{url_for("movies")}"</script>'
        else:
            flash("로그인 실패!", 'error')
    return render_template('movie_login.html')
from flask import request


### 회원가입
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('username')
        id = request.form.get('userid')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        file = request.files['file']
        
        filename = file.filename if file else None
        if filename:
            file_path = os.path.join(app.config['USER_IMAGE_FOLDER'], filename)
            file.save(file_path)
            
        if manager.duplicate_user(id):
            flash("중복된 아이디가 존재합니다.",'error')
            return redirect(url_for('register'))

        if password == confirm_password:
            manager.regsiter_user(name, id, password,user_ip,filename)
            return redirect(url_for('login'))
        return flash("계정 등록 실패,400", "error")
    return render_template('movie_register.html')


### 로그아웃
@app.route('/logout')
def delete_session_data():
    session.clear()
    flash("로그아웃 되었습니다.", "success")
    return render_template('movie_login.html')

### 내정보
@app.route('/myinfo')
def myinfo():
    id = session['id']
    user = manager.get_user_by_id(id)
    return render_template('movie_myinfo.html',user=user)

@app.route('/userinfo/<user_id>')
def user_info(user_id):
    id = session['id']
    user = manager.get_user_by_id(user_id)
    return render_template('movie_myinfo.html',user=user,id=id)

### 회원 탈퇴
@app.route('/delete_user')
def delete_user():
    id = session['id']
    if manager.delete_user(id):
        session.clear()
        return f'<script>alert("회원탈퇴 성공!");location.href="{url_for("login")}"</script>' # 스크립트로 alert알람창 띄우기
    else:
        return f'<script>alert("회원탈퇴 실패!");location.href="{url_for("index")}"</script>'
    
### 회원 탈퇴(신고 추방)
@app.route('/user/delete/<user_id>')
def report_user(user_id):
    if manager.delete_user(user_id):
        flash(f"{user_id}계정이 삭제되었습니다.",'success')
        return redirect(request.referrer or url_for('movie_report'))
    else:
        flash(f"{user_id}계정 삭제를 실패했습니다.",'error')
        return redirect(request.referrer or url_for('movie_report'))

### 비밀번호 변경
@app.route('/edit_password', methods=['GET','POST'])
def edit_password():
    if request.method=='POST':
        id = request.form.get('userid')
        password = request.form.get('password')
        user = manager.get_user_by_id(id)
        if user['id'] == request.form.get('userid') and user['name'] == request.form.get('username'):
            if manager.get_user_edit_password(id, password):
                return f'<script>alert("비밀번호 변경 성공!");location.href="{url_for("login")}"</script>'
            return f'<script>alert("비밀번호 변경 실패!, 아이디 혹은 이름이 다릅니다.");location.href="{url_for("login")}"</script>'
    return render_template('movie_edit_password.html')

### 상영중인 영화 당일 랭킹순으로 화면에 표현
@app.route('/movies')
@app.route('/')
def movies():
    manager.update_movie_ratings_and_reviews()
    movies = manager.get_all_movies()
    movies_info = []
    for movie in movies:
        print(movie)
        movies_info.append({'id':movie['id'],"title":movie['title'],"rank":movie['rank'],"filename":movie['filename'],"rating":movie['rating'],"reviews":movie['reviews']})

    return render_template('movie_movies.html', movies_info=movies_info)

### 해당영화 리뷰
@app.route('/reviews/<title>')
def review(title):
    all_posts = manager.get_all_posts()
    posts=[]
    for post in all_posts:
        if post['movie_title'] == title:
            posts.append(post)  
    page = int(request.args.get('page', 1))  # 쿼리 파라미터에서 페이지 번호 가져오기
    per_page = 5
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = posts[start:end]
    # 총 페이지 수 계산
    total_pages = (len(posts) + per_page - 1) // per_page
    return render_template('movie_review.html',title=title, posts=paginated_data, page=page, total_pages=total_pages)

### 모든 리뷰 보여주는 페이지
@app.route('/all_reviews')
def all_reviews():
    posts = manager.get_all_posts()

    page = int(request.args.get('page', 1))  # 쿼리 파라미터에서 페이지 번호 가져오기
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = posts[start:end]
    # 총 페이지 수 계산
    total_pages = (len(posts) + per_page - 1) // per_page
    return render_template('movie_review.html', posts=paginated_data, page=page, total_pages=total_pages)

### 선택한 리뷰 상세히 보기
@app.route('/post/<title>/<int:id>')
@login_required
def view_post(id,title):
    post = manager.get_post_by_id(id)
    views = manager.increment_hits(id)
    all_comments = manager.get_all_comments()
    comments = []
    for comment in all_comments:
        if comment['post_id'] == id:
            comments.append(comment)
    return render_template('movie_view.html',title=title,post=post, views=views, comments=comments)


### 리뷰 추가
### 파일업로드: method='POST' enctype="multipart/form-data" type='file accept= '.png,.jpg,.gif
@app.route('/post/add/<movie_title>', methods=['GET', 'POST'])
@login_required
def add_post(movie_title):
    userid = session.get('id')
    username = session.get('name')
    user_img = session.get('filename')

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('review_content')
        rating = request.form.get('rating')
        spoiler = bool(request.form.get('spoiler'))
        file = request.files.get('file')
        filename = None
        if file and file.filename:
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

        if manager.insert_post(title, content, filename, userid, username, rating, spoiler, movie_title):
            flash("리뷰가 성공적으로 추가되었습니다!", "success")
            return redirect(f'/reviews/{movie_title}')
        else:
            flash("리뷰 추가 실패!", "error")
            return redirect(request.url)

    return render_template('movie_review_add.html', movie_title=movie_title)

### 리뷰 수정
@app.route('/post/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files['file']
        
        filename = file.filename if file else None
        
        if filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        
        # 게시글 정보를 업데이트
        if manager.update_post(id, title, content, filename):
            flash("업데이트 성공!", "success")
            return redirect(url_for('movies'))  # 성공 시 메인 페이지로 리디렉션
        return flash("게시글 수정 실패,400", 'error')  # 실패 시 400 에러 반환

    # GET 요청: 게시글 정보를 가져와 폼에 표시
    post = manager.get_post_by_id(id)
    if post:
        return render_template('movie_edit.html', post=post)  # 수정 페이지 렌더링
    return flash("게시글을 찾을 수 없습니다.404", 'error')

### 리뷰 삭제
@app.route('/post/delete/<int:id>')
def delete_post(id):
    post = manager.get_post_by_id(id)
    if post:
        file = post.get('filename')
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            os.remove(file_path)
            flash("file삭제",'success')
            if manager.delete_post(id):
                flash("게시물 삭제 성공!","success")
                return redirect(url_for('index'))
            return f'<script>alert("파일 삭제 성공! 게시물 삭제 실패!");location.href="{url_for("register")}"</script>' # 스크립트로 alert알람창 띄우기
        else:
            if manager.delete_post(id):
                flash("게시물 삭제 성공!","success")
                return redirect(url_for('index'))
        flash("삭제실패",'error')
    
    return redirect(url_for('view'))

### 영화 랭킹(일일 관객수, 누적 관객수, 일일 매출액, 누적 매출액) 시각화
@app.route('/movie_ranks')
def movie_ranks():
    movie_infos = manager.get_all_movies()
    page_title = 'Movie_Ranks'
    title = [movie_info['title'] for movie_info in movie_infos]
    t_sales = [movie_info['t_sales'] for movie_info in movie_infos]
    c_sales = [movie_info['c_sales'] for movie_info in movie_infos]
    t_audience = [movie_info['t_audience'] for movie_info in movie_infos]
    c_audience = [movie_info['c_audience'] for movie_info in movie_infos]

    # 전체 데이터를 JSON으로 전달
    movies_data = [
        {
            "title": movie_info['title'],
            "t_sales": movie_info['t_sales'],
            "c_sales": movie_info['c_sales'],
            "t_audience": movie_info['t_audience'],
            "c_audience": movie_info['c_audience']
        }
        for movie_info in movie_infos
    ]
    return render_template(
        'movie_ranks.html',
        page_title = page_title,
        movies_data=movies_data,
        title=title,
        t_sales=t_sales,
        c_sales=c_sales,
        t_audience=t_audience,
        c_audience=c_audience
    )        

### 카카오 지도로 가까운 영화관 검색 
@app.route('/movie_map')
def movie_map():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    loc = manager.loc_ip(user_ip)
    return render_template('movie_map.html', loc= loc)

### 영화별 예고편
@app.route('/movie_youtube/<title>')
def movie_youtube(title):
    return render_template('movie_youtube.html',title=title)

@app.route('/post/recommend/<int:post_id>/<title>')
def recommend_post(post_id,title):
    manager.recommend_post(post_id)
    # 추천 후 목록 페이지로 리디렉션
    return redirect(request.referrer or url_for('view_post', id=id))


@app.route('/post/report/<movie_title>/<int:post_id>/<writer_id>', methods=['GET', 'POST'])
def report_post(movie_title,post_id,writer_id):
        

    if request.method == 'POST':
        # 신고 내용 및 사유 저장
        content = request.form.get('content')
        reason_code = request.form.get('reason')  # 체크박스에서 선택한 값
        reporter_id = request.form.get('user_id')
        if not content or not reason_code:
            flash('신고 내용을 작성하고 사유를 선택해주세요.', 'danger')
            return redirect(url_for('report_post',movie_title=movie_title, post_id=post_id,writer_id=writer_id))
        manager.report_post_count(post_id)
        manager.report_post(post_id,reporter_id, content, reason_code,movie_title,writer_id)

        return redirect(url_for('movies'))  # 신고 후 목록 페이지로 리디렉션
    return render_template('movie_report.html',movie_title=movie_title, post_id=post_id,writer_id=writer_id)

@app.route('/movie_review_rank')
def movie_review_rank():
    posts = manager.get_all_posts()
    tops = []
    recommend = []
    for post in posts:
        tops.append({
            'user_id': post['userid'],
            'title': post['title'],
            'movie_title': post['movie_title'],
            'views': post['views'],
            'recommend': post['recommend'],
            'comments': post['comment']
            })
    top_views = sorted(tops, key=lambda x: x['views'], reverse=True)[:10]
    top_recommend = sorted(tops, key=lambda x: x['recommend'], reverse=True)[:10]
    top_comments = sorted(tops, key=lambda x: x['comments'], reverse=True)[:10]
    return render_template('movie_review_rank.html', top_views = top_views, top_recommend=top_recommend, top_comments=top_comments)



@app.route('/post/<int:id>/comment', methods = ['POST'])
def movie_review_comment(id):
    # 댓글 저장 로직
    # 예: DB에 댓글 추가
    content = request.form.get('content')
    if content:
        # DB에 저장하는 로직 (예시)
        manager.insert_comment(post_id=id, user_id=session['id'],user_name=session['name'], content=content)
    manager.comment_post_count(id)
    # 사용자가 왔던 페이지로 리다이렉트
    return redirect(request.referrer or url_for('view_post', id=id))


### 댓글 삭제
@app.route('/post/comment_delete/<int:id>/<int:comment_id>')
def delete_comment(id,comment_id):
    comment = manager.get_comment_by_id(comment_id)
    if comment:
        manager.delete_comment(comment_id)
        flash("댓글 삭제 성공!","success")
        return redirect(request.referrer or url_for('view_post', id=id))
    flash("삭제실패",'error')
    return redirect(request.referrer or url_for('view_post', id=id))

@app.route('/reports')
def movie_report():
    reports = manager.view_reports()
    return render_template('movie_reports.html',reports=reports)

@app.route('/show_movie_about')
def index():
    return render_template('movie_about.html')

@app.route('/movie_about')
def movie_about():
    try:
        # 절대 경로로 CSV 파일 읽기
        base_dir = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(base_dir, "static/csv/movie_data_2010_to_present.csv")
        data = pd.read_csv(file_path)

        # 날짜 데이터 변환
        data['date'] = pd.to_datetime(data['date'], format='%Y%m%d', errors='coerce')
        data['year'] = data['date'].dt.year

        # 코로나 전후 평균값 계산
        pre_covid = data[data['year'] < 2020]
        post_covid = data[data['year'] >= 2020]
        pre_covid_avg = pre_covid['audiCnt'].mean()
        post_covid_avg = post_covid['audiCnt'].mean()

        # 넷플릭스 전후 평균값 계산
        pre_netflix = data[data['year'] < 2016]
        post_netflix = data[data['year'] >= 2016]
        pre_netflix_avg = pre_netflix['audiCnt'].mean()
        post_netflix_avg = post_netflix['audiCnt'].mean()

        # 연도별 평균 관람객 계산
        yearly_avg = data.groupby('year')['audiCnt'].mean().reset_index()

        # JSON 데이터 반환
        response = {
            "pre_post_covid": [pre_covid_avg, post_covid_avg],
            "pre_post_netflix": [pre_netflix_avg, post_netflix_avg],
            "yearly_avg": yearly_avg.to_dict(orient='records')
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/movie_notice')
def movie_notice():
    return render_template('movie_notice.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)