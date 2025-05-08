document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('import-form');
  
    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
  
        const formData = new FormData(form);
  
        fetch('/datasetimporter/form', {
          method: 'POST',
          body: formData
        })
        .then(res => res.json())
        .then(data => {
          const link = `/datasetimporter/status?task=${data.task_id}`;
          const container = document.getElementById('progress-link');
          const linkEl = document.getElementById('link-text');
  
          linkEl.href = link;
          linkEl.innerText = window.location.origin + link;
          container.style.display = 'block';
        })
        .catch(err => {
          alert("Something went wrong: " + err);
        });
      });
    }
  });
  