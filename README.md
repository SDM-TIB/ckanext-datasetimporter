# 📦 DatasetImporter Plugin for CKAN

A CKAN plugin to import multiple JSON-based datasets in bulk by uploading a ZIP file through a user-friendly form interface. Supports real-time status tracking and controlled access (admin-only).

---

## 👤 User Guide

### 1. Access the Import Page
Only admin users can access the DatasetImporter interface. You'll find a new button near the "Batch Import" button.

### 2. Fill the Form
You will need to:

- 📁 **Upload a ZIP file**: containing one or more JSON dataset metadata files.
- 🏢 **Select an organization**: this will be the owner of all datasets.
- 🏷️ **Enter a prefix**: added before each dataset name to ensure uniqueness.
- 🗂️ **Enter repository name**: to tag all datasets accordingly.

### 3. Submit & Track Progress
After clicking Submit:
- You’ll see a unique status link.
- Copy and bookmark it if needed.
- Visit it anytime to see how your upload is progressing.

---

## ⚙️ Developer Installation Guide

### Requirements

- CKAN 2.9+
- Docker-based CKAN setup recommended

### Installation Steps

1. Clone this plugin into your extensions directory:
   ```bash
   git clone https://github.com/SDM-TIB/ckanext-datasetimporter ckanext-datasetimporter
   ```

2. Install the plugin:
   ```bash
   pip install -e .
   ```

3. Enable it in your CKAN config:
   ```ini
   ckan.plugins = datasetimporter
   ```

4. Rebuild the CKAN container:
   ```bash
   docker compose restart ckan
   ```

5. (Optional) Create the `/srv/app/tmp` and `LOG/` folders if not present.

6. Overwrite the following file to integrate the DatasetImporter button:
   Replace:
   ```
   src/ckanext-gitImport/ckanext/gitimport/templates/snippets/add_dataset.html
   ```
   with:
   ```
   additions/add_dataset.html

---

## 📁 Plugin Structure

```
ckanext-datasetimporter/
│
├── templates/
│   └── datasetimporter/
│       ├── form.html        # The upload form
│       └── status.html      # The status tracker
│
├── public/
│   └── js/
│       └── form_logic.js    # JS logic for frontend updates
│
├── logic/
│   └── insert.py            # Core logic to process and insert datasets
│
├── views.py                 # Flask Blueprint endpoints
└── plugin.py                # CKAN plugin class
```

---

## 🔐 Access Control

- The plugin checks that only sysadmin users can access the form.
- Non-admins will receive a 403 message with instructions to contact the site admin.

---

## 🤝 Contributing

Contributions are welcome. Fork the repo and open a pull request.

---

