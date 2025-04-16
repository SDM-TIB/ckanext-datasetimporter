import os
import subprocess
import ckan.model as model
from flask import Blueprint, request, redirect, flash
from ckan.plugins import toolkit
from werkzeug.utils import secure_filename
from ckan.common import config
import threading
import uuid

task_status = {}


datasetimporter = Blueprint("datasetimporter", __name__)

@datasetimporter.route("/datasetimporter/form", methods=["GET", "POST"])
def show_form():
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user or toolkit.c.author or 'default'
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
          extract_path = os.path.join(upload_dir, os.path.splitext(filename)[0])
          with zipfile.ZipFile(save_path, "r") as zip_ref:
             zip_ref.extractall(extract_path)
        else:
          extract_path = upload_dir
        
        def process_background(task_id, extract_path, organization, repo_name):
            try:
    
                task_status[task_id] = "📦 Processing datasets…"
        
                from ckanext.datasetimporter.logic.insert import process_folder
                process_folder(extract_path, organization, repo_name)

                task_status[task_id] = "🔁 Reindexing CKAN…"

                subprocess.run([
    "ckan", "-c", "/root/ckan/etc/default/ckan.ini", "search-index", "rebuild", "-o"
])


                task_status[task_id] = "✅ Done! Datasets are now available."

            except Exception as e:
                task_status[task_id] = f"❌ Error: {str(e)}"

        threading.Thread(target=process_background, args=(task_id, extract_path, organization, repo_name)).start()
        return redirect(f"/datasetimporter/status?task={task_id}")         

    return toolkit.render("datasetimporter/form.html", extra_vars={"orgs": orgs})

@datasetimporter.route("/datasetimporter/status", methods=["GET"])
def check_status():
    task_id = request.args.get("task")
    status = task_status.get(task_id, "Unknown task ID.")
    return status
