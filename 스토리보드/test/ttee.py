import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
from datetime import datetime, timedelta

class AgroBuddyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AgroBuddy - 스마트 농업 도우미")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        self.current_user = None # 현재 로그인된 사용자 ID
        self.current_selected_crop = None # 현재 선택된 작물

        self.init_db() # 데이터베이스 초기화

        self.create_login_screen() # 앱 시작 시 로그인 화면 먼저 표시

    def init_db(self):
        """SQLite 데이터베이스 초기화 및 테이블 생성"""
        conn = sqlite3.connect('agrobuddy.db')
        c = conn.cursor()

        # 사용자 테이블 생성 (id, password)
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')

        # 작물 재배 정보 테이블 생성
        # (user_id, crop_name, start_date, progress, pot_size, water_amount, water_frequency, soil_type)
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_crops (
                user_id TEXT,
                crop_name TEXT,
                start_date TEXT,
                progress INTEGER DEFAULT 0,
                pot_size TEXT,
                water_amount TEXT,
                water_frequency TEXT,
                soil_type TEXT,
                PRIMARY KEY (user_id, crop_name),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
        conn.close()

    def register_user(self):
        """회원가입 처리"""
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("입력 오류", "아이디와 비밀번호를 모두 입력해주세요.")
            return

        conn = sqlite3.connect('agrobuddy.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (id, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("회원가입 성공", f"'{username}'님 환영합니다! 로그인 해주세요.")
            # 회원가입 성공 후 로그인 화면으로 자동 전환
            self.show_login_frame()
        except sqlite3.IntegrityError:
            messagebox.showerror("회원가입 실패", "이미 존재하는 아이디입니다. 다른 아이디를 사용해주세요.")
        finally:
            conn.close()

    def login_user(self):
        """로그인 처리"""
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("입력 오류", "아이디와 비밀번호를 모두 입력해주세요.")
            return

        conn = sqlite3.connect('agrobuddy.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            self.current_user = username
            messagebox.showinfo("로그인 성공", f"'{username}'님 안녕하세요!")
            self.create_main_app_widgets() # 로그인 성공 시 메인 앱 위젯 생성
            self.main_app_frame.pack(fill=tk.BOTH, expand=True) # 메인 앱 화면 표시
            self.login_frame.pack_forget() # 로그인 화면 숨기기
            self.update_crop_list() # 로그인 후 작물 목록 업데이트
        else:
            messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 올바르지 않습니다.")

    def create_login_screen(self):
        """로그인/회원가입 화면 생성"""
        self.login_frame = ttk.Frame(self.root, padding="20")
        self.login_frame.pack(fill=tk.BOTH, expand=True)

        # 로그인 섹션
        login_section = ttk.LabelFrame(self.login_frame, text="로그인", padding="15")
        login_section.pack(pady=20, padx=50, fill=tk.X)

        ttk.Label(login_section, text="아이디:").pack(pady=5)
        self.login_username_entry = ttk.Entry(login_section, width=30)
        self.login_username_entry.pack(pady=5)

        ttk.Label(login_section, text="비밀번호:").pack(pady=5)
        self.login_password_entry = ttk.Entry(login_section, show="*", width=30)
        self.login_password_entry.pack(pady=5)

        ttk.Button(login_section, text="로그인", command=self.login_user).pack(pady=15)

        # 회원가입 섹션
        reg_section = ttk.LabelFrame(self.login_frame, text="회원가입", padding="15")
        reg_section.pack(pady=20, padx=50, fill=tk.X)

        ttk.Label(reg_section, text="새 아이디:").pack(pady=5)
        self.reg_username_entry = ttk.Entry(reg_section, width=30)
        self.reg_username_entry.pack(pady=5)

        ttk.Label(reg_section, text="새 비밀번호:").pack(pady=5)
        self.reg_password_entry = ttk.Entry(reg_section, show="*", width=30)
        self.reg_password_entry.pack(pady=5)

        ttk.Button(reg_section, text="회원가입", command=self.register_user).pack(pady=15)

        self.login_username_entry.focus_set() # 시작 시 아이디 입력창에 포커스

    def show_login_frame(self):
        """로그인 화면을 다시 표시 (회원가입 후 등)"""
        if hasattr(self, 'main_app_frame'):
            self.main_app_frame.pack_forget()
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        self.login_username_entry.delete(0, tk.END)
        self.login_password_entry.delete(0, tk.END)
        self.reg_username_entry.delete(0, tk.END)
        self.reg_password_entry.delete(0, tk.END)


    def create_main_app_widgets(self):
        """로그인 성공 후 메인 앱의 위젯들을 생성합니다."""
        self.main_app_frame = ttk.Frame(self.root, padding="10")
        # 이 프레임은 로그인 성공 시 pack 됩니다.

        self.notebook = ttk.Notebook(self.main_app_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.create_start_screen()
        self.create_add_crop_screen() # 작물 추가 화면 추가
        self.create_crop_recommendation_screen()
        self.create_cultivation_guide_screen()
        self.create_diagnosis_screen()
        self.create_solution_screen()
        self.create_chatbot_screen()

        # 로그아웃 버튼 추가 (메인 앱 프레임에)
        ttk.Button(self.main_app_frame, text="로그아웃", command=self.logout).pack(side=tk.TOP, anchor=tk.NE, padx=5, pady=5)


    def logout(self):
        """로그아웃 처리"""
        self.current_user = None
        messagebox.showinfo("로그아웃", "로그아웃 되었습니다.")
        self.show_login_frame() # 로그인 화면으로 돌아가기


    def create_start_screen(self):
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="내 농장")

        ttk.Label(frame, text=f"🏡 {self.current_user}님의 농장 🏡", font=("Helvetica", 22, "bold")).pack(pady=20)

        # 내 작물 목록 표시 영역
        ttk.Label(frame, text="🌱 나의 재배 작물 🌱", font=("Helvetica", 16, "bold")).pack(pady=15)
        self.crop_list_frame = ttk.Frame(frame, padding="10", relief="groove", borderwidth=1)
        self.crop_list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 작물 목록을 표시할 캔버스 및 스크롤바
        self.crop_canvas = tk.Canvas(self.crop_list_frame)
        self.crop_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.crop_scrollbar = ttk.Scrollbar(self.crop_list_frame, orient="vertical", command=self.crop_canvas.yview)
        self.crop_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.crop_canvas.configure(yscrollcommand=self.crop_scrollbar.set)
        self.crop_canvas.bind('<Configure>', lambda e: self.crop_canvas.configure(scrollregion = self.crop_canvas.bbox("all")))

        self.inner_crop_frame = ttk.Frame(self.crop_canvas)
        self.crop_canvas.create_window((0, 0), window=self.inner_crop_frame, anchor="nw")

        self.update_crop_list() # 작물 목록 업데이트 호출

        # 내 작물 추가 버튼
        ttk.Button(frame, text="+ 내 작물 추가", command=lambda: self.notebook.select(self.notebook.tabs()[1])).pack(pady=20)


    def update_crop_list(self):
        """현재 사용자의 작물 목록을 DB에서 불러와 화면에 표시"""
        for widget in self.inner_crop_frame.winfo_children():
            widget.destroy() # 기존 위젯 삭제

        conn = sqlite3.connect('agrobuddy.db')
        c = conn.cursor()
        c.execute("SELECT crop_name, start_date, progress FROM user_crops WHERE user_id=?", (self.current_user,))
        crops = c.fetchall()
        conn.close()

        if not crops:
            ttk.Label(self.inner_crop_frame, text="아직 등록된 작물이 없습니다.\n'+ 내 작물 추가' 버튼을 눌러 시작해보세요!", font=("Helvetica", 12), foreground="gray").pack(pady=30)
        else:
            for i, crop in enumerate(crops):
                crop_name, start_date_str, progress = crop

                # 진행도 계산 (예시: 시작일로부터 경과 일수)
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                today = datetime.now()
                # 임의의 총 재배 기간 (예: 90일)
                total_growth_days = 90
                elapsed_days = (today - start_date).days
                
                # 진행도는 DB에 저장된 값 또는 계산된 값 중 선택
                # 여기서는 DB 저장된 값(progress)을 우선 사용하거나, 경과 일수로 계산된 값을 사용
                calculated_progress = min(100, max(0, int((elapsed_days / total_growth_days) * 100)))
                
                # DB의 progress 값이 있으면 그 값을 사용, 없으면 계산된 값 사용
                actual_progress = progress if progress is not None else calculated_progress


                crop_item_frame = ttk.Frame(self.inner_crop_frame, relief="solid", borderwidth=1, padding=10)
                crop_item_frame.pack(fill=tk.X, pady=5, padx=5)

                ttk.Label(crop_item_frame, text=f"작물명: {crop_name}", font=("Helvetica", 14, "bold")).pack(anchor=tk.W)
                ttk.Label(crop_item_frame, text=f"시작일: {start_date_str}", font=("Helvetica", 10)).pack(anchor=tk.W)

                # 진행도 바
                progress_bar = ttk.Progressbar(crop_item_frame, orient="horizontal", length=300, mode="determinate", value=actual_progress)
                progress_bar.pack(pady=5, anchor=tk.W)
                ttk.Label(crop_item_frame, text=f"진행도: {actual_progress}%", font=("Helvetica", 10)).pack(anchor=tk.W)
                
                # 상세 보기 버튼 (클릭 시 해당 작물의 재배 가이드로 이동)
                ttk.Button(crop_item_frame, text="재배 가이드 보기", command=lambda name=crop_name: self.show_cultivation_guide(name)).pack(pady=5, anchor=tk.E)

        # 캔버스 스크롤 영역 재설정
        self.crop_canvas.update_idletasks()
        self.crop_canvas.config(scrollregion=self.crop_canvas.bbox("all"))

    def show_cultivation_guide(self, crop_name):
        """특정 작물의 재배 가이드 화면으로 이동하고 정보 로드"""
        self.current_selected_crop = crop_name
        self.notebook.select(self.notebook.tabs()[3]) # 재배 가이드 탭으로 이동
        # 재배 가이드 탭으로 이동한 후, 해당 작물 정보를 불러와서 표시하는 로직이 create_cultivation_guide_screen 내부에 필요함

    def create_add_crop_screen(self):
        """새로운 작물 추가 화면 생성"""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="작물 추가")

        ttk.Label(frame, text="➕ 내 작물 등록하기 ➕", font=("Helvetica", 18, "bold")).pack(pady=20)

        # 작물 이름
        ttk.Label(frame, text="작물 이름:").pack(pady=5)
        self.new_crop_name_entry = ttk.Entry(frame, width=40)
        self.new_crop_name_entry.pack(pady=5)

        # 재배 시작일
        ttk.Label(frame, text="재배 시작일 (YYYY-MM-DD):").pack(pady=5)
        self.start_date_entry = ttk.Entry(frame, width=40)
        self.start_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d')) # 오늘 날짜 기본값
        self.start_date_entry.pack(pady=5)

        # 상세 재배 정보 입력 필드
        ttk.Label(frame, text="화분 크기 (예: 15cm):").pack(pady=5)
        self.pot_size_entry = ttk.Entry(frame, width=40)
        self.pot_size_entry.pack(pady=5)

        ttk.Label(frame, text="물의 양 (예: 200ml):").pack(pady=5)
        self.water_amount_entry = ttk.Entry(frame, width=40)
        self.water_amount_entry.pack(pady=5)

        ttk.Label(frame, text="물 주는 주기 (예: 3일):").pack(pady=5)
        self.water_frequency_entry = ttk.Entry(frame, width=40)
        self.water_frequency_entry.pack(pady=5)

        ttk.Label(frame, text="흙 종류 (예: 배양토):").pack(pady=5)
        self.soil_type_entry = ttk.Entry(frame, width=40)
        self.soil_type_entry.pack(pady=5)


        ttk.Button(frame, text="작물 등록", command=self.save_new_crop).pack(pady=30)
        ttk.Button(frame, text="내 농장으로 돌아가기", command=lambda: self.notebook.select(self.notebook.tabs()[0])).pack(pady=10)

    def save_new_crop(self):
        """새로운 작물 정보를 DB에 저장"""
        crop_name = self.new_crop_name_entry.get().strip()
        start_date = self.start_date_entry.get().strip()
        pot_size = self.pot_size_entry.get().strip()
        water_amount = self.water_amount_entry.get().strip()
        water_frequency = self.water_frequency_entry.get().strip()
        soil_type = self.soil_type_entry.get().strip()

        if not all([crop_name, start_date]):
            messagebox.showwarning("입력 오류", "작물 이름과 시작일을 입력해주세요.")
            return

        try:
            # 날짜 형식 검증
            datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("날짜 형식 오류", "재배 시작일을 YYYY-MM-DD 형식으로 입력해주세요.")
            return

        conn = sqlite3.connect('agrobuddy.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO user_crops (user_id, crop_name, start_date, progress, pot_size, water_amount, water_frequency, soil_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (self.current_user, crop_name, start_date, 0, pot_size, water_amount, water_frequency, soil_type))
            conn.commit()
            messagebox.showinfo("등록 성공", f"'{crop_name}' 작물이 등록되었습니다.")
            self.new_crop_name_entry.delete(0, tk.END)
            self.start_date_entry.delete(0, tk.END)
            self.start_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
            self.pot_size_entry.delete(0, tk.END)
            self.water_amount_entry.delete(0, tk.END)
            self.water_frequency_entry.delete(0, tk.END)
            self.soil_type_entry.delete(0, tk.END)

            self.update_crop_list() # 작물 목록 새로고침
            self.notebook.select(self.notebook.tabs()[0]) # 내 농장 탭으로 돌아가기
        except sqlite3.IntegrityError:
            messagebox.showerror("등록 실패", "이미 등록된 작물입니다. 다른 이름으로 등록해주세요.")
        finally:
            conn.close()


    def create_crop_recommendation_screen(self):
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="작물 추천") # 탭 이름 변경

        ttk.Label(frame, text="🌱 현재 날씨 기반 농작물 추천 🌱", font=("Helvetica", 18, "bold")).pack(pady=20)

        tk.Label(frame, text="[현재 날씨 정보 표시 공간]", font=("Helvetica", 12), background="lightgray", width=60, height=5).pack(pady=10)
        ttk.Label(frame, text="온도: 25°C, 습도: 70%, 강수량: 0mm, 일조량: 8시간 (가정치)", font=("Helvetica", 10)).pack()

        ttk.Label(frame, text="[추천 농작물 목록]", font=("Helvetica", 14, "bold")).pack(pady=15)
        ttk.Label(frame, text="1. 토마토 (생육 적합도: 높음)", font=("Helvetica", 12)).pack(anchor=tk.W, padx=50)
        ttk.Label(frame, text="2. 상추 (생육 적합도: 보통)", font=("Helvetica", 12)).pack(anchor=tk.W, padx=50)
        ttk.Label(frame, text="3. 고추 (생육 적합도: 낮음)", font=("Helvetica", 12)).pack(anchor=tk.W, padx=50)

        # 버튼 문구 및 이동 탭 변경
        ttk.Button(frame, text="선택한 작물 재배 가이드 보기", command=lambda: self.show_cultivation_guide("토마토 (예시)")).pack(pady=30)
        # 실제 구현에서는 선택된 작물 이름을 넘겨야 함
        ttk.Button(frame, text="메인으로 돌아가기", command=lambda: self.notebook.select(self.notebook.tabs()[0])).pack(pady=10)


    def create_cultivation_guide_screen(self):
        self.cultivation_guide_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.cultivation_guide_frame, text="재배 가이드")

        self.guide_title_label = ttk.Label(self.cultivation_guide_frame, text="📋 맞춤형 농작물 재배 가이드라인 📋", font=("Helvetica", 18, "bold"))
        self.guide_title_label.pack(pady=20)
        
        self.crop_name_guide_label = ttk.Label(self.cultivation_guide_frame, text="[선택된 농작물: 정보 없음]", font=("Helvetica", 14, "bold"))
        self.crop_name_guide_label.pack(pady=10)

        self.guide_details_text = scrolledtext.ScrolledText(self.cultivation_guide_frame, wrap=tk.WORD, width=70, height=15, font=("Helvetica", 10))
        self.guide_details_text.pack(pady=10)
        self.guide_details_text.insert(tk.END, "작물을 선택하시면 상세 가이드가 표시됩니다.")
        self.guide_details_text.config(state=tk.DISABLED) # 텍스트 편집 불가

        ttk.Button(self.cultivation_guide_frame, text="다른 작물 추천 보기", command=lambda: self.notebook.select(self.notebook.tabs()[2])).pack(side=tk.LEFT, padx=10, pady=20)
        ttk.Button(self.cultivation_guide_frame, text="작물 상태 진단하기", command=lambda: self.notebook.select(self.notebook.tabs()[4])).pack(side=tk.RIGHT, padx=10, pady=20)
        ttk.Button(self.cultivation_guide_frame, text="내 농장으로 돌아가기", command=lambda: self.notebook.select(self.notebook.tabs()[0])).pack(pady=10)

        # 탭 선택 이벤트 바인딩: 탭이 선택될 때마다 내용 업데이트
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_select)

    def on_tab_select(self, event):
        """탭이 변경될 때 호출되어 재배 가이드 내용을 업데이트합니다."""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if selected_tab == "재배 가이드" and self.current_selected_crop:
            self.load_cultivation_guide_content(self.current_selected_crop)

    def load_cultivation_guide_content(self, crop_name):
        """DB에서 작물 정보를 불러와 재배 가이드 내용을 업데이트"""
        conn = sqlite3.connect('agrobuddy.db')
        c = conn.cursor()
        c.execute("SELECT pot_size, water_amount, water_frequency, soil_type FROM user_crops WHERE user_id=? AND crop_name=?", (self.current_user, crop_name))
        crop_info = c.fetchone()
        conn.close()

        self.guide_details_text.config(state=tk.NORMAL)
        self.guide_details_text.delete(1.0, tk.END)

        if crop_info:
            pot_size, water_amount, water_frequency, soil_type = crop_info
            self.crop_name_guide_label.config(text=f"[선택된 농작물: {crop_name}]")
            
            # 임의의 재배 단계별 가이드라인
            guide_content = f"""
**선택된 작물: {crop_name}**

---
**기본 정보:**
- **화분 크기:** {pot_size if pot_size else "정보 없음"}
- **물의 양:** {water_amount if water_amount else "정보 없음"}
- **물 주는 주기:** {water_frequency if water_frequency else "정보 없음"}
- **흙 종류:** {soil_type if soil_type else "정보 없음"}

---
**오늘 해야 할 일:**
- {crop_name} 모종 주변 흙에 물을 충분히 주세요. (물의 양: {water_amount if water_amount else "확인 필요"}, 주기: {water_frequency if water_frequency else "확인 필요"})
- 병충해 예방을 위해 통풍이 잘 되는지 확인하세요.

**이번 주 해야 할 일:**
- {crop_name} 지지대가 필요하다면 설치하여 쓰러지지 않도록 고정해주세요.
- 첫 꽃이 피면 영양분 공급을 위해 유기질 비료를 소량 시비해주세요.
- 곁가지(순지르기)를 제거하여 주 줄기에 영양분이 집중되도록 합니다.

**흙 관리:**
- {soil_type if soil_type else "선택된 흙"}의 상태를 정기적으로 확인하고, 필요 시 비료를 추가하거나 보충해주세요.
- 흙이 너무 마르지 않도록 주의하고, 과습하지 않도록 배수에 신경 쓰세요.

---
**참고:**
- 이 가이드라인은 일반적인 정보이며, 실제 재배 환경에 따라 조절이 필요할 수 있습니다.
- 작물 상태에 이상이 있다면 '작물 상태 진단' 기능을 이용해보세요.
            """
            self.guide_details_text.insert(tk.END, guide_content)
        else:
            self.crop_name_guide_label.config(text=f"[선택된 농작물: {crop_name} - 정보 부족]")
            self.guide_details_text.insert(tk.END, "해당 작물에 대한 상세 재배 정보가 없습니다. '작물 추가' 탭에서 정보를 입력해주세요.")

        self.guide_details_text.config(state=tk.DISABLED)


    def create_diagnosis_screen(self):
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="작물 진단")

        ttk.Label(frame, text="📸 사용자 사진 기반 작물 상태 진단 📸", font=("Helvetica", 18, "bold")).pack(pady=20)

        ttk.Label(frame, text="작물 사진을 업로드 해주세요.", font=("Helvetica", 12)).pack(pady=10)

        # 이미지 업로드 버튼 및 미리보기 공간
        ttk.Button(frame, text="사진 업로드", command=self.upload_photo).pack(pady=10)
        tk.Label(frame, text="[업로드된 이미지 미리보기 공간]", background="lightgray", width=60, height=15).pack(pady=10)

        ttk.Button(frame, text="진단 시작", command=lambda: self.notebook.select(self.notebook.tabs()[5])).pack(pady=20) # 문제 해결 탭으로 이동
        ttk.Button(frame, text="내 농장으로 돌아가기", command=lambda: self.notebook.select(self.notebook.tabs()[0])).pack(pady=10)

    def upload_photo(self):
        # 실제 앱에서는 파일 선택 대화 상자를 띄우고 이미지를 처리합니다.
        # 여기서는 스토리보드 목적이므로 기능 없음
        print("사진 업로드 기능 (실제 구현 필요)")
        messagebox.showinfo("알림", "사진 업로드 기능은 현재 스토리보드용입니다. 실제 구현이 필요합니다.")
        pass

    def create_solution_screen(self):
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="문제 해결")

        ttk.Label(frame, text="🔍 진단 결과 및 해결 방안 제시 💡", font=("Helvetica", 18, "bold")).pack(pady=20)
        ttk.Label(frame, text="[진단 결과: 토마토 잎의 검은 반점 (예시)]", font=("Helvetica", 14, "bold")).pack(pady=10)

        diagnosis_result_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=70, height=8, font=("Helvetica", 10))
        diagnosis_result_text.pack(pady=10)
        diagnosis_result_text.insert(tk.END, """
**진단 결과:**
- 잎에 검은 반점이 보입니다.
- **곰팡이병 (역병) 초기 증상**일 수 있습니다.

**성장 저해 요인:**
- 높은 습도와 불충분한 통풍
- 병원균 감염
        """)
        diagnosis_result_text.config(state=tk.DISABLED)

        solution_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=70, height=8, font=("Helvetica", 10))
        solution_text.pack(pady=10)
        solution_text.insert(tk.END, """
**해결 방안:**
1.  **감염된 잎 제거:** 즉시 감염된 잎과 가지를 잘라내어 병의 확산을 막아주세요. 제거한 부분은 다른 작물에 옮지 않도록 소각하거나 밀봉하여 버려야 합니다.
2.  **통풍 개선:** 작물 간 간격을 조절하고, 주변 잡초를 제거하여 공기 순환을 원활하게 해주세요.
3.  **친환경 살균제 살포:** 초기 증상이므로 베이킹소다 희석액 (물 1L에 베이킹소다 5g)을 잎 앞뒷면에 고르게 살포해보세요. 증상이 심하면 전문 살균제를 사용해야 합니다.
4.  **물 주기 조절:** 잎에 물이 닿지 않도록 뿌리에 직접 물을 주고, 흙이 충분히 마른 후 다시 물을 주세요.
        """)
        solution_text.config(state=tk.DISABLED)

        ttk.Button(frame, text="내 농장으로 돌아가기", command=lambda: self.notebook.select(self.notebook.tabs()[0])).pack(side=tk.LEFT, padx=10, pady=20)
        ttk.Button(frame, text="챗봇에게 추가 문의", command=lambda: self.notebook.select(self.notebook.tabs()[6])).pack(side=tk.RIGHT, padx=10, pady=20)


    def create_chatbot_screen(self):
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="챗봇 상담")

        ttk.Label(frame, text="💬 AI 챗봇 농업 상담 💬", font=("Helvetica", 18, "bold")).pack(pady=20)

        # 채팅 기록을 표시할 Text 위젯
        self.chat_history = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=70, height=20, font=("Helvetica", 10), state=tk.DISABLED)
        self.chat_history.pack(pady=10, fill=tk.BOTH, expand=True)

        # 사용자 입력 프레임
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=10)

        self.user_input_entry = ttk.Entry(input_frame, width=60, font=("Helvetica", 10))
        self.user_input_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.user_input_entry.bind("<Return>", self.send_message) # Enter 키로 메시지 전송

        send_button = ttk.Button(input_frame, text="전송", command=self.send_message)
        send_button.pack(side=tk.RIGHT)

        # 초기 챗봇 메시지
        self.display_message("AgroBuddy 챗봇", "안녕하세요! 농업에 대해 궁금한 점을 물어보세요.", "bot")
        ttk.Button(frame, text="내 농장으로 돌아가기", command=lambda: self.notebook.select(self.notebook.tabs()[0])).pack(pady=10)


    def send_message(self, event=None): # event=None은 bind 함수에서 호출될 때 인자를 받기 위함
        user_message = self.user_input_entry.get()
        if user_message.strip():
            self.display_message("나", user_message, "user")
            self.user_input_entry.delete(0, tk.END)

            bot_response = self.get_chatbot_response(user_message)
            self.display_message("AgroBuddy 챗봇", bot_response, "bot")

    def display_message(self, sender, message, message_type):
        """채팅 기록창에 메시지를 추가합니다."""
        self.chat_history.config(state=tk.NORMAL) # 쓰기 가능하게 변경
        timestamp = datetime.now().strftime("[%H:%M]")

        if message_type == "user":
            self.chat_history.insert(tk.END, f"{timestamp} {sender}: ", "user_tag")
            self.chat_history.insert(tk.END, f"{message}\n\n", "user_msg_tag")
        else: # bot
            self.chat_history.insert(tk.END, f"{timestamp} {sender}: ", "bot_tag")
            self.chat_history.insert(tk.END, f"{message}\n\n", "bot_msg_tag")

        self.chat_history.config(state=tk.DISABLED) # 다시 쓰기 불가능하게 변경
        self.chat_history.see(tk.END) # 스크롤을 항상 최하단으로

        # 태그 스타일 정의 (선택 사항: 글자색, 볼드체 등)
        self.chat_history.tag_config("user_tag", foreground="blue", font=("Helvetica", 10, "bold"))
        self.chat_history.tag_config("user_msg_tag", foreground="black", font=("Helvetica", 10))
        self.chat_history.tag_config("bot_tag", foreground="green", font=("Helvetica", 10, "bold"))
        self.chat_history.tag_config("bot_msg_tag", foreground="black", font=("Helvetica", 10))


    def get_chatbot_response(self, user_message):
        """사용자 메시지에 대한 챗봇 응답을 생성합니다. (임시 로직)"""
        user_message = user_message.lower().strip()

        if "안녕" in user_message or "hi" in user_message:
            return "안녕하세요! 무엇을 도와드릴까요?"
        elif "날씨" in user_message:
            return "현재 날씨 정보를 원하시면 '작물 추천' 탭을 확인해 주세요. 더 자세한 정보가 필요하신가요?"
        elif "병충해" in user_message or "진단" in user_message:
            return "작물 사진을 '작물 진단' 탭에 올려주시면 상태를 진단해 드릴 수 있습니다."
        elif "재배" in user_message or "가이드" in user_message:
            if self.current_selected_crop:
                return f"현재 선택된 작물 '{self.current_selected_crop}'에 대한 재배 가이드는 '재배 가이드' 탭에서 보실 수 있습니다."
            else:
                return "재배 가이드는 '재배 가이드' 탭에서 선택한 작물에 맞춰 제공됩니다."
        elif "화분 크기" in user_message or "흙" in user_message or "물 주기" in user_message:
            return "화분 크기, 물 주기, 흙 종류 등의 상세 재배 정보는 '작물 추가' 탭에서 등록하실 수 있으며, '재배 가이드' 탭에서 확인 가능합니다."
        elif "고마워" in user_message or "감사" in user_message:
            return "천만에요! 더 궁금한 점이 있으시면 언제든지 물어보세요."
        else:
            return "질문을 정확히 이해하지 못했습니다. 좀 더 구체적으로 말씀해 주시거나, 다른 탭의 기능을 이용해 보세요."


    def upload_photo(self):
        print("사진 업로드 기능 (실제 구현 필요)")
        messagebox.showinfo("알림", "사진 업로드 기능은 현재 스토리보드용입니다. 실제 구현이 필요합니다.")
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = AgroBuddyApp(root)
    root.mainloop()