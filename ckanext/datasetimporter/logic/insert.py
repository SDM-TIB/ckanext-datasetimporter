# ckanext/datasetimporter/logic/insert.py

import os, json, uuid
import psycopg2
from datetime import datetime

def process_folder(folder_path, organization_id, repo_name):
    conn = psycopg2.connect(
        dbname="ckan",
        user="ckan",
        password="ckan",
        host="db",
        port="5432"
    )
    cur = conn.cursor()

    def log_skip(file_path, reason):
        with open("/srv/app/skipped.txt", "a", encoding="utf-8") as f:
            f.write(f"{file_path} - {reason}\n")

    def slugify(text):
        import re
        return re.sub(r'[^a-z0-9-_]', '-', text.lower())

    def truncate(text, max_length):
        return text[:max_length] if text and len(text) > max_length else text

    def insert_extra(package_id, key, value):
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        cur.execute("""
            INSERT INTO package_extra (id, package_id, key, value, state)
            VALUES (%s, %s, %s, %s, 'active')
        """, (
            str(uuid.uuid4()), package_id, key, value
        ))

    def insert_dataset_from_json(json_path, org_id, repo_name):
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        result = raw.get("result", {})

        dataset_id = str(uuid.uuid4())
        name = truncate(slugify("tytyty_" + result.get("id", str(uuid.uuid4()))), 100)
        url = result.get("resource") or "https://example.com"
        title = result.get("title", {}).get("en") or result.get("title", {}).get("de") or "Untitled"
        description = result.get("description")
        notes = (description.get("en") or description.get("de")) if isinstance(description, dict) else "No description"

        creator = result.get("creator")
        author = creator.get("name", "Unknown Author") if isinstance(creator, dict) else creator or "Unknown Author"
        created = datetime.now()
        owner_org = organization_id  # org_id will be passed as argument


        cur.execute("SELECT 1 FROM package WHERE name = %s", (name,))
        if cur.fetchone():
            print(f"Dataset '{name}' already exists. Skipping.")
            return

        cur.execute("""
            INSERT INTO package (
                id, name, title, notes, author, url,
                metadata_created, metadata_modified,
                private, state, owner_org, type
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            dataset_id, name, title, notes, author, url,
            created, created, False, 'active', owner_org, 'vdataset'
        ))

        lang = 'Deutsch' if 'de' in (result.get("title") or {}) else 'English'
        insert_extra(dataset_id, "repository_name", repo_name)
        insert_extra(dataset_id, "language", lang)
        for key in ['defined_in', 'doi', 'conformsTo']:
            val = result.get(key)
            if val:
                insert_extra(dataset_id, key, val)

        publisher = result.get("publisher")
        publisher_name = publisher.get("name", "Unknown") if isinstance(publisher, dict) else publisher or "Unknown"
        insert_extra(dataset_id, "publisher", publisher_name)

        location = result.get("spatial") or result.get("location")
        if location:
            insert_extra(dataset_id, "location", "Defined in GeoJSON")

        # Resources
        distributions = result.get("distributions", [])
        if not isinstance(distributions, list):
            distributions = []

        for i, dist in enumerate(distributions):
            res_id = str(uuid.uuid4())
            res_name = dist.get("title", {}).get("en") or dist.get("title", {}).get("de") or f"Resource {i}"
            res_desc = dist.get("description", {}).get("en") or dist.get("description", {}).get("de") or "No description"
            res_format = dist.get("format", {}).get("label", "Unknown")
            res_url = dist.get("access_url", [""])[0] if isinstance(dist.get("access_url"), list) else dist.get("access_url", "")

            cur.execute("""
                INSERT INTO resource (
                    id, package_id, url, format, description,
                    name, created, last_modified, state, position
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                res_id, dataset_id, res_url, res_format, res_desc,
                res_name, created, created, 'active', i
            ))

        conn.commit()

    # Main loop
    for file in os.listdir(folder_path):
        if file.endswith(".json"):
            json_path = os.path.join(folder_path, file)
            try:
                insert_dataset_from_json(json_path, organization_id, repo_name)
            except Exception as e:
                print(f"⚠️ Skipped {file}: {e}")
                log_skip(file, str(e))

    cur.close()
    conn.close()
