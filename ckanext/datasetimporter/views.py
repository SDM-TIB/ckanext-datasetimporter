import sys
import os

# Ensure the LOG directory exists
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(BASE_DIR, "LOG")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "views_log.txt")

# Redirect stdout and stderr to the log file
sys.stdout = open(log_file, "w", encoding="utf-8")
sys.stderr = sys.stdout


import subprocess
import ckan.model as model
from flask import Blueprint, request, redirect, flash, jsonify
from ckan.plugins import toolkit
from werkzeug.utils import secure_filename
from ckan.plugins.toolkit import abort, check_access
from ckan.common import config
import threading
import uuid

task_status = {}


datasetimporter = Blueprint("datasetimporter", __name__)

@datasetimporter.route("/datasetimporter/form", methods=["GET", "POST"])
def show_form():
    user = toolkit.c.user or toolkit.c.author or 'default'

    try:
        check_access('sysadmin', {'user': user})
    except toolkit.NotAuthorized:
        abort(403, 'This plugin is restricted to admin users. Contact your administrator for access.')

    context = {
        'model': model,
        'session': model.Session,
        'user': user
    }

    # GET logic first (to avoid crashing if POST fails)
    try:
        orgs = toolkit.get_action("organization_list")(context, {"all_fields": True})
        print(f"✅ Loaded {len(orgs)} organizations.")
    except Exception as e:
        orgs = []
        print(f"❌ Failed to load organizations: {e}")

    if request.method == "POST":
        # Generate a task ID
        task_id = str(uuid.uuid4())
        task_status[task_id] = "Starting import…"
        uploaded_file = request.files.get("folder")
        organization = request.form.get("organization")
        prefix = request.form.get("prefix")
        repo_name = request.form.get("repo_name")

        if not uploaded_file:
            flash("No folder uploaded", "error")
            return redirect(request.url)
        upload_dir = "/srv/app/tmp"
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(uploaded_file.filename)
        save_path = os.path.join(upload_dir, filename)
        uploaded_file.save(save_path)

# Determine extraction path here too
        if filename.endswith(".zip"):
          import zipfile
          
          with zipfile.ZipFile(save_path, "r") as zip_ref:
             extract_path = os.path.join(upload_dir, os.path.splitext(filename)[0])
             zip_ref.extractall(extract_path)
        else:
          extract_path = upload_dir
        
        def process_background(task_id, extract_path, organization, repo_name):
            try:
                
                BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                log_dir = os.path.join(BASE_DIR, "LOG")
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, "views_log.txt")
                sys.stdout = open(log_file, "a", encoding="utf-8")
                sys.stderr = sys.stdout
                task_status[task_id] = "📦 Processing datasets…"
        
                from ckanext.datasetimporter.logic.insert import process_folder
                process_folder(extract_path, organization, repo_name, prefix)

                task_status[task_id] = "🔁 Reindexing CKAN…"

                subprocess.run([
                      "ckan", "-c", "/root/ckan/etc/default/ckan.ini", "search-index", "rebuild", "-o"
                    ])


                task_status[task_id] = "✅ Done! Datasets are now available."

            except Exception as e:
                task_status[task_id] = f"❌ Error: {str(e)}"

        threading.Thread(target=process_background, args=(task_id, extract_path, organization, repo_name)).start()
        return jsonify({"task_id": task_id})
         

    return toolkit.render("datasetimporter/form.html", extra_vars={"orgs": orgs})

@datasetimporter.route("/datasetimporter/status", methods=["GET"])
def check_status():
    task_id = request.args.get("task")
    status = task_status.get(task_id, "Unknown task ID.")

    return toolkit.render(
        "datasetimporter/status.html",
        extra_vars={"status": status, "task_id": task_id}
    )

