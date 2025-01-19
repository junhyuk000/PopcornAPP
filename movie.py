from flask import Flask, url_for, render_template, send_from_directory, jsonify ,request, redirect, session,flash
from functools import wraps
import os
from datetime import datetime
from models import DBManager


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


# 지정된 디렉토리에서 image 파일 제공
@app.route('/images/<path:filename>')
def img_file(filename):
    return send_from_directory('static/images', filename)

@app.route('/js/<path:filename>')
def js_file(filename):
    return send_from_directory('static/js', filename)

@app.route('/user_image/<path:filename>')
def user_img_file(filename):
    return send_from_directory('static/user_image', filename)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/uploads/<path:filename>')
def uploads_file(filename):
    return send_from_directory('static/uploads', filename)

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

@app.route('/post/<title>/<int:id>')
@login_required
def view_post(id,title):
    post = manager.get_post_by_id(id)
    views = manager.increment_hits(id)
    return render_template('movie_view.html',title=title,post=post, views=views)



# 내용추가
# 파일업로드: method='POST' enctype="multipart/form-data" type='file accept= '.png,.jpg,.gif
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
            return redirect(url_for('index'))  # 성공 시 메인 페이지로 리디렉션
        return flash("게시글 수정 실패,400", 'error')  # 실패 시 400 에러 반환

    # GET 요청: 게시글 정보를 가져와 폼에 표시
    post = manager.get_post_by_id(id)
    if post:
        return render_template('movie_edit.html', post=post)  # 수정 페이지 렌더링
    return flash("게시글을 찾을 수 없습니다.404", 'error')

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
            return f'<script>alert("파일 삭제 성공! 게시물 삭제 실패!");location.href="{url_for('register')}"</script>' # 스크립트로 alert알람창 띄우기
        else:
            if manager.delete_post(id):
                flash("게시물 삭제 성공!","success")
                return redirect(url_for('index'))
        flash("삭제실패",'error')
    
    return redirect(url_for('view'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('username')
        id = request.form.get('userid')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        user_ip = request.remote_addr
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

@app.route('/login', methods=['GET','POST'])
@app.route('/')
def login():

    if request.method == 'POST':
        id = request.form.get('userid')
        password = request.form.get('password')
        user = manager.login_user(id, password)
        if user:
            session['id'] = id
            session['name'] = user['name']
            session['filename'] = user['filename']
            
            return f'<script>alert("로그인 성공!");location.href="{url_for('movies')}"</script>'
        else:
            flash("로그인 실패!", 'error')
    return render_template('movie_login.html')

@app.route('/movie_ranks')
def movie_ranks():
    movie_infos = manager.get_all_movies()

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
        movies_data=movies_data,
        title=title,
        t_sales=t_sales,
        c_sales=c_sales,
        t_audience=t_audience,
        c_audience=c_audience
    )



@app.route('/audience_rank')
def audience_rank():
    movie_names = ["Movie1", "Movie2", "Movie3"]
    daily_audience = [1200, 1500, 1800]
    return render_template('movie_audience_rank.html', movie_names=movie_names, daily_audience=daily_audience)

@app.route('/movies')
def movies():
    movies = manager.get_all_movies()
    movies_info = []
    for movie in movies:
        movies_info.append({'id':movie['id'],"title":movie['title'],"rank":movie['rank'],"filename":movie['filename']})

    return render_template('movie_movies.html', movies_info=movies_info)

### 세션 삭제
@app.route('/logout')
def delete_session_data():
    session.clear()
    flash("로그아웃 되었습니다.", "success")
    return render_template('movie_login.html')

@app.route('/myinfo')
def myinfo():
    id = session['id']
    user = manager.get_user_by_id(id)
    return render_template('movie_myinfo.html',user=user)

@app.route('/delete_user')
def delete_user():
    id = session['id']
    if manager.delete_user(id):
        session.clear()
        return f'<script>alert("회원탈퇴 성공!");location.href="{url_for('login')}"</script>' # 스크립트로 alert알람창 띄우기
    else:
        return f'<script>alert("회원탈퇴 실패!");location.href="{url_for('index')}"</script>'

@app.route('/edit_password', methods=['GET','POST'])
def edit_password():
    if request.method=='POST':
        id = request.form.get('userid')
        password = request.form.get('password')
        user = manager.get_user_by_id(id)
        if user['id'] == request.form.get('userid') and user['name'] == request.form.get('username'):
            if manager.get_user_edit_password(id, password):
                return f'<script>alert("비밀번호 변경 성공!");location.href="{url_for('login')}"</script>'
            return f'<script>alert("비밀번호 변경 실패!, 아이디 혹은 이름이 다릅니다.");location.href="{url_for('login')}"</script>'
        
    return render_template('movie_edit_password.html')
        

@app.route('/movie_map')
def movie_map():

    return render_template('movie_map.html')

@app.route('/movie_youtube/<title>')
def movie_youtube(title):
    return render_template('movie_youtube.html',title=title)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)