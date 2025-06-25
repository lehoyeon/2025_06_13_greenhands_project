import os

def find_html_files(directory):
    """HTML 파일들을 찾아서 위치 표시"""
    html_files = []
    
    print(f"📁 {directory} 폴더 구조:")
    print("=" * 50)
    
    try:
        for root, dirs, files in os.walk(directory):
            level = root.replace(directory, '').count(os.sep)
            indent = "  " * level
            folder_name = os.path.basename(root) if root != directory else "ROOT"
            print(f"{indent}📁 {folder_name}/")
            
            sub_indent = "  " * (level + 1)
            for file in files:
                if file.endswith(('.html', '.htm')):
                    html_files.append(os.path.join(root, file))
                    print(f"{sub_indent}🌐 {file} ⭐")
                elif file.endswith(('.css', '.js')):
                    print(f"{sub_indent}📄 {file}")
                elif file.endswith(('.py', '.pkl', '.h5', '.npy')):
                    print(f"{sub_indent}🔧 {file}")
                else:
                    print(f"{sub_indent}📄 {file}")
    
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    print("\n" + "=" * 50)
    print("🌐 발견된 HTML 파일들:")
    if html_files:
        for html_file in html_files:
            print(f"  - {html_file}")
    else:
        print("  HTML 파일을 찾을 수 없습니다.")
    
    return html_files

# 폴더 구조 확인
base_dir = r"C:\ydata-profiling\2025_06_13\CropGrowthSimul_deep"
html_files = find_html_files(base_dir)

# Flask 표준 구조 확인
templates_dir = os.path.join(base_dir, "templates")
static_dir = os.path.join(base_dir, "static")

print(f"\n📋 Flask 구조 체크:")
print(f"  templates/ 폴더 존재: {'✅' if os.path.exists(templates_dir) else '❌'}")
print(f"  static/ 폴더 존재: {'✅' if os.path.exists(static_dir) else '❌'}")

if html_files:
    print(f"\n💡 권장사항:")
    print(f"  1. HTML 파일들을 {templates_dir} 폴더로 이동")
    print(f"  2. CSS/JS 파일들을 {static_dir} 폴더로 이동")
    print(f"  3. app.py에서 render_template() 사용")