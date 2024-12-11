from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_cors import CORS  # Import the CORS module
import os
import logging
import webbrowser
import threading

# 创建 Flask 应用
app = Flask(__name__, static_folder='static', template_folder='templates')

# Enable CORS for all origins or specify a certain origin
CORS(app, origins=["http://localhost:63342"])  # Allow requests from your frontend URL

# 指定共享文件夹路径
SHARED_FOLDER = "/Users/jinceyang/RiderProjects/addressables_test/ServerData"

# 检查目录是否存在
if not os.path.exists(SHARED_FOLDER):
    print(f"The directory {SHARED_FOLDER} does not exist. Please create it or specify a valid path.")
    exit(1)

# 配置日志记录
LOG_FILE = "server.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_request(action, path=None):
    """
    记录日志信息
    """
    ip = request.remote_addr
    log_message = f"IP: {ip} - Action: {action}"
    if path:
        log_message += f" - Path: {path}"
    logging.info(log_message)

def get_folder_contents(folder_path):
    """
    获取文件夹内容
    """
    try:
        items = os.listdir(folder_path)
        result = {"files": [], "directories": []}
        for item in items:
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                result["files"].append(item)
            elif os.path.isdir(item_path):
                result["directories"].append(item)
        return result
    except Exception as e:
        logging.error(f"Error listing folder contents: {str(e)}")
        raise

@app.route("/", defaults={"subpath": ""}, methods=["GET"])
@app.route("/<path:subpath>", methods=["GET"])
def list_folder_contents(subpath):
    """
    列出共享文件夹及其子目录中的内容
    """
    folder_path = os.path.join(SHARED_FOLDER, subpath)

    if not os.path.exists(folder_path):
        return jsonify({"error": "Directory not found"}), 404

    if not os.path.isdir(folder_path):
        # 如果是文件，则直接下载
        return serve_file(subpath)

    try:
        log_request("List folder contents", subpath)
        contents = get_folder_contents(folder_path)
        return jsonify({"path": subpath, "files": contents["files"], "directories": contents["directories"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload_file():
    """
    接收文件上传
    """
    subpath = request.args.get("path", "")  # 上传时附带目标路径
    upload_folder = os.path.join(SHARED_FOLDER, subpath)

    if not os.path.exists(upload_folder):
        return jsonify({"error": "Target folder does not exist"}), 404

    if "file" not in request.files:
        logging.warning("No file part in the request")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        logging.warning("No selected file")
        return jsonify({"error": "No selected file"}), 400

    # 保存文件
    try:
        save_path = os.path.join(upload_folder, file.filename)
        file.save(save_path)
        log_request("Upload file", os.path.join(subpath, file.filename))
        return jsonify({"message": "File uploaded successfully", "filename": file.filename}), 201
    except Exception as e:
        logging.error(f"Error uploading file: {str(e)}")
        return jsonify({"error": "File upload failed", "details": str(e)}), 500

def serve_file(file_path):
    """
    提供文件下载功能
    """
    try:
        directory, filename = os.path.split(file_path)
        log_request("Download file", file_path)
        return send_from_directory(os.path.join(SHARED_FOLDER, directory), filename, as_attachment=True)
    except FileNotFoundError:
        logging.warning(f"File not found: {file_path}")
        return jsonify({"error": "File not found"}), 404

# 新增：默认加载 index.html 页面
@app.route("/index", methods=["GET"])
def index():
    """
    返回首页（index.html）
    """
    return render_template("index.html")

def open_browser():
    """
    自动打开浏览器
    """
    webbrowser.open("http://127.0.0.1:8085/index")

if __name__ == "__main__":
# 清空日志文件内容
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w'):
            pass  # Opening the file in write mode clears its contents
    threading.Timer(1.25, open_browser).start()
    # 设置服务器监听所有地址，端口为8085
    app.run(host="127.0.0.1", port=8085, debug=True)
